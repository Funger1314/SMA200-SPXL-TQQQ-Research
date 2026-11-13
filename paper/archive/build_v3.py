"""Assemble research_paper_v3.md from the template + generated tables, then build PDF and DOCX."""
import re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'research_paper_v3.template.md').read_text()
t=re.sub(r'\{\{table:(\w+)\}\}',lambda m:(P/'tables'/f'{m.group(1)}.md').read_text().strip(),t)
(P/'research_paper_v3.md').write_text(t)
common=['research_paper_v3.md','--from','markdown+tex_math_dollars+pipe_tables','--resource-path',str(P)]
subprocess.run(['pandoc',*common,'--pdf-engine=xelatex','-V','mainfont=DejaVu Serif','-V','monofont=DejaVu Sans Mono','-o','SMA200_Leveraged_ETF_Research_v3.pdf'],cwd=P,check=True)
subprocess.run(['pandoc',*common,'-o','SMA200_Leveraged_ETF_Research_v3.docx'],cwd=P,check=True)
print('built')
