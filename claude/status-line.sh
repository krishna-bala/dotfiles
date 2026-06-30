#!/bin/bash

# Parse input JSON from Claude. Single jq pass: this script runs on every
# status refresh, so one fork instead of one per field. Fields are joined
# with the \x1f unit separator (a non-whitespace IFS char, so empty fields
# survive read's word splitting).
input=$(cat)
IFS=$'\x1f' read -r current_dir worktree ctx_used_pct ctx_total_in ctx_window_size \
	cache_read model_name five_hr five_hr_reset seven_day seven_day_reset < <(
	echo "$input" | jq -r '[
		(.workspace.current_dir // ""),
		(.workspace.git_worktree // ""),
		(.context_window.used_percentage // ""),
		(.context_window.total_input_tokens // ""),
		(.context_window.context_window_size // ""),
		(.context_window.current_usage.cache_read_input_tokens // ""),
		(.model.display_name // .model.id // ""),
		(.rate_limits.five_hour.used_percentage // ""),
		(.rate_limits.five_hour.resets_at // ""),
		(.rate_limits.seven_day.used_percentage // ""),
		(.rate_limits.seven_day.resets_at // "")
	] | map(tostring) | join("\u001f")'
)

# Get username and hostname
username=$(whoami)
hostname_short=$(hostname -s)

# Get git branch if in a git repository
branch=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
	branch=$(git branch --show-current 2>/dev/null || echo "HEAD")
fi

# Replace $HOME with ~
display_dir="${current_dir/#$HOME/\~}"

# If inside a linked worktree, strip the .worktrees/<name> segment so the
# path reads like the main checkout; the worktree name is shown as a badge.
if [ -n "$worktree" ]; then
	needle="/.worktrees/$worktree"
	display_dir="${display_dir/$needle/}"
fi

# Fish-style abbreviation: keep the last segment full; abbreviate every
# ancestor to its first character (preserving a leading dot for hidden dirs).
fish_abbrev() {
	local path="$1" leading="" rest="" last=""
	if [[ "$path" == "~"* ]]; then
		leading="~"
		rest="${path:1}"
	elif [[ "$path" == /* ]]; then
		leading=""
		rest="$path"
	else
		rest="$path"
	fi
	# Strip leading slash for splitting
	rest="${rest#/}"
	IFS='/' read -ra parts <<< "$rest"
	local n=${#parts[@]}
	if [ "$n" -eq 0 ]; then
		echo "$leading"
		return
	fi
	last="${parts[$((n-1))]}"
	local out="$leading"
	for (( i=0; i<n-1; i++ )); do
		local p="${parts[$i]}"
		[ -z "$p" ] && continue
		if [[ "$p" == .* ]]; then
			out="${out}/${p:0:2}"
		else
			out="${out}/${p:0:1}"
		fi
	done
	echo "${out}/${last}"
}
truncated_dir=$(fish_abbrev "$display_dir")

# Build colored output
GIT_BRANCH_GLYPH='🌿'
WORKTREE_GLYPH='🌲'
# Leading reset prevents terminal state bleeding into the status line
output=$(printf "\033[0m\033[1;32m%s@%s\033[0m \033[1;34m%s\033[0m" \
	"$username" \
	"$hostname_short" \
	"$truncated_dir")

if [ -n "$worktree" ] && [ -n "$branch" ]; then
	output=$(printf "%s\n\033[1;33m%s %s\033[0m \033[0m|\033[0m \033[1;35m%s %s\033[0m" "$output" "$WORKTREE_GLYPH" "$worktree" "$GIT_BRANCH_GLYPH" "$branch")
elif [ -n "$worktree" ]; then
	output=$(printf "%s\n\033[1;33m%s %s\033[0m" "$output" "$WORKTREE_GLYPH" "$worktree")
elif [ -n "$branch" ]; then
	output=$(printf "%s\n\033[1;35m%s %s\033[0m" "$output" "$GIT_BRANCH_GLYPH" "$branch")
fi

# Format a resets_at ISO timestamp as a human-readable countdown
format_countdown() {
	local resets_at="$1"
	[ -z "$resets_at" ] && return
	local reset_epoch now_epoch diff_s
	# Handle Unix timestamp (seconds or milliseconds) or ISO string
	if [[ "$resets_at" =~ ^[0-9]+$ ]]; then
		if [ ${#resets_at} -ge 13 ]; then
			reset_epoch=$((resets_at / 1000))
		else
			reset_epoch=$resets_at
		fi
	else
		reset_epoch=$(date -d "$resets_at" +%s 2>/dev/null) || return
	fi
	now_epoch=$(date +%s)
	diff_s=$((reset_epoch - now_epoch))
	[ "$diff_s" -le 0 ] && echo "now" && return
	local days hours mins
	days=$((diff_s / 86400))
	hours=$(( (diff_s % 86400) / 3600 ))
	mins=$(( (diff_s % 3600) / 60 ))
	if [ "$days" -gt 0 ]; then
		printf "%dd %dh" "$days" "$hours"
	elif [ "$hours" -gt 0 ]; then
		printf "%dh %dm" "$hours" "$mins"
	else
		printf "%dm" "$mins"
	fi
}

# Color a percentage: red >=80, yellow >=50, cyan otherwise
color_pct() {
	local pct="$1"
	if [ "$pct" -ge 80 ]; then
		printf "\033[1;31m%s%%\033[0m" "$pct"
	elif [ "$pct" -ge 50 ]; then
		printf "\033[1;33m%s%%\033[0m" "$pct"
	else
		printf "\033[1;32m%s%%\033[0m" "$pct"
	fi
}

# Context window usage (added in CC 2.1.129)
if [ -n "$ctx_used_pct" ]; then
	ctx_pct=$(printf "%.0f" "$ctx_used_pct")
	fmt_tokens() {
		local n="$1"
		if [ "$n" -ge 1000 ]; then
			printf "%dk" $(( n / 1000 ))
		else
			printf "%d" "$n"
		fi
	}
	if [ -n "$ctx_total_in" ] && [ "$ctx_total_in" -ge 500000 ]; then
		ctx_color="\033[1;31m"
	elif [ -n "$ctx_total_in" ] && [ "$ctx_total_in" -ge 300000 ]; then
		ctx_color="\033[1;33m"
	else
		ctx_color="\033[1;32m"
	fi
	if [ -n "$model_name" ]; then
		output=$(printf "%s\n\033[0m%s | " "$output" "$model_name")
	else
		output=$(printf "%s\n\033[0m" "$output")
	fi
	if [ -n "$ctx_total_in" ]; then
		output=$(printf "%s%s (${ctx_color}%s%%\033[0m)" "$output" "$(fmt_tokens "$ctx_total_in")" "$ctx_pct")
		# Cache split: ⚡ tokens read from cache, ↑ non-cached input tokens
		cache_read="${cache_read%%.*}"
		if [[ "$cache_read" =~ ^[0-9]+$ ]]; then
			non_cached=$((${ctx_total_in%%.*} - cache_read))
			[ "$non_cached" -lt 0 ] && non_cached=0
			output=$(printf "%s \033[2m⚡%s ↑%s\033[0m" "$output" "$(fmt_tokens "$cache_read")" "$(fmt_tokens "$non_cached")")
		fi
	else
		output=$(printf "%s${ctx_color}%s%%\033[0m" "$output" "$ctx_pct")
	fi
fi

# Rate limit usage (added in CC 2.1.80)
if [ -n "$five_hr" ] || [ -n "$seven_day" ]; then
	rl_parts=()
	if [ -n "$five_hr" ]; then
		pct=$(printf "%.0f" "$five_hr")
		countdown=$(format_countdown "$five_hr_reset")
		part=$(printf "\033[0m5h: %s" "$(color_pct "$pct")")
		[ -n "$countdown" ] && part=$(printf "%s \033[2m(%s)\033[0m" "$part" "$countdown")
		rl_parts+=("$part")
	fi
	if [ -n "$seven_day" ]; then
		pct=$(printf "%.0f" "$seven_day")
		countdown=$(format_countdown "$seven_day_reset")
		part=$(printf "\033[0m7d: %s" "$(color_pct "$pct")")
		[ -n "$countdown" ] && part=$(printf "%s \033[2m(%s)\033[0m" "$part" "$countdown")
		rl_parts+=("$part")
	fi
	rl_str="${rl_parts[0]}  ${rl_parts[1]}"
	[ -z "${rl_parts[1]}" ] && rl_str="${rl_parts[0]}"
	output=$(printf "%s \033[0m|\033[0m %s" "$output" "$rl_str")
fi

# Always end with a reset so nothing bleeds past the status line
printf "%s\033[0m\n" "$output"
