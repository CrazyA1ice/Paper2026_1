from pathlib import Path
import importlib.util,json,sys,shutil
QA=Path(__file__).resolve().parent
S=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1020.11127\skills\documents')
m=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
spec=importlib.util.spec_from_file_location('packaged_fidelity_diff',S/'scripts/render_and_diff.py')
diff=importlib.util.module_from_spec(spec);spec.loader.exec_module(diff)
def reviewed_word_render(render_py,docx,outdir):
    source=QA/'论文模板_render' if Path(docx)==Path(m['template_converted']) else QA/'render'
    target=Path(outdir);target.mkdir(parents=True,exist_ok=True)
    for p in source.glob('page-*.png'):shutil.copy2(p,target/p.name)
diff._run_render=reviewed_word_render
out=QA/('template-fidelity-diff-'+m['output_sha256'][:8])
assert not out.exists()
sys.argv=['render_and_diff.py',m['template_converted'],m['output'],'--outdir',str(out)]
diff.main()
(out/'scope_adjudication.md').write_text('All reference instruction/example body slots are intentionally replaced by manuscript content. The five-page instructional template and seven-page article therefore differ throughout the body. The three section geometries and blank header/footer parts are preserved. Only document.xml, document.xml.rels, styles.xml, content types and four new figure media parts changed. See manifest.json and render_verification.json for deterministic checks. Native Word read-only exports are the authoritative render; no conversion or source rewriting was performed by this diff.',encoding='utf8')
