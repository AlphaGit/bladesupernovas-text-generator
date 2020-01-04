wget https://gist.githubusercontent.com/h3xx/1976236/raw/bbabb412261386673eff521dddbe1dc815373b1d/wiki-100k.txt
wget https://nlp.stanford.edu/data/wordvecs/glove.6B.zip
unzip -q glove.6B.zip -d .
python -m gensim.scripts.glove2word2vec --input  glove.6B.50d.txt --output glove_model.txt

# Initial test corpora: The Adventures of Sherlock Holmes
wget https://www.gutenberg.org/files/1661/1661-0.txt