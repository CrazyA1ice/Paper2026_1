from pathlib import Path
import fitz
root = Path("paper_template/长春工程学院学报(自然科学版)")
output=Path("review_scratch/journal_sample_review_20261022")
output.mkdir(parents=True,exist_ok=True)
names = [
("AES","基于AES的网络安全态势感知数据多层次加密方法_胡艳.pdf"),
("PSO","基于PSO的PC构件生产系统人员柔性调度优化研究_原丕业.pdf"),
("图书分类","基于关键词提取模型与强化学习的高校图书馆图书自动分类方法_庄辉凤.pdf")
]
for short,name in names:
    doc=fitz.open(root/name)
    pages=[]
    for j,p in enumerate(doc):
        pages.append("=== PAGE "+str(j+1)+" ===\n"+p.get_text(sort=True))
        if j==0 or j==min(2,len(doc)-1):
            pix=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
            pix.save(str(output/(short+"_"+str(j+1)+".png")))
    (output/(short+".txt")).write_text("\n\n".join(pages),encoding="utf-8")
    print(short,len(doc),sum(len(x) for x in pages),[tuple(p.rect) for p in doc][:1])
