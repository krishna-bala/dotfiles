#!/usr/bin/env python3
"""Keep AGENTS.md primary; recognize legacy CLAUDE.md in unmigrated projects."""
import re, tomllib
from pathlib import Path

def configure(text):
    before=tomllib.loads(text)
    values=before.get('project_doc_fallback_filenames',[])
    if 'CLAUDE.md' in values:return text
    import json
    values=[*values,'CLAUDE.md']
    line='project_doc_fallback_filenames = '+json.dumps(values)+'\n'
    if 'project_doc_fallback_filenames' in before:
        # Refuse complex formatting rather than rewrite unrelated settings.
        text,n=re.subn(r'^project_doc_fallback_filenames\s*=\s*\[[^\n]*\][^\n]*\n?',line,text,count=1,flags=re.M)
        if n!=1:raise ValueError('Existing fallback setting requires manual review')
    else:text=line+text
    after=tomllib.loads(text);expected=dict(before);expected['project_doc_fallback_filenames']=values
    assert after==expected
    return text

if __name__=='__main__':
    p=Path.home()/'.codex/config.toml';s=p.read_text();out=configure(s)
    if out!=s:p.write_text(out)
    print('AGENTS.md remains primary; CLAUDE.md is a fallback.')
