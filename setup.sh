if [ ! -f wiki-100k.txt ]; then
    echo "Downloading wiki100k most used terms..."
    wget https://gist.githubusercontent.com/h3xx/1976236/raw/bbabb412261386673eff521dddbe1dc815373b1d/wiki-100k.txt
fi

if [ ! -f glove.6B.zip ]; then
    echo "Downloading GloVe 6B parameters, pretrained model."
    wget https://nlp.stanford.edu/data/wordvecs/glove.6B.zip
    echo "Unzupping GloVe pretrained model."
    unzip -q glove.6B.zip -d .
fi

if [ ! -f 1661-0.txt ]; then
    echo "Downloading initial text corpora for training."
    # Initial test corpora: The Adventures of Sherlock Holmes
    wget https://www.gutenberg.org/files/1661/1661-0.txt
fi

CONDA_ENVS=$(conda env list | awk '{print $1}')
if ! [[ $CONDA_ENVS = *"text-generator"* ]]; then
    echo "Creating conda text-generator environment."
    conda env create -f environment.yml
fi

conda activate text-generator

if [ ! -f glove_model.txt ]; then
    echo "Translating GloVe into Word2Vec"
    python -m gensim.scripts.glove2word2vec --input  glove.6B.50d.txt --output glove_model.txt
fi