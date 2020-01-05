if [ ! -f data/wiki-100k.txt ]; then
    echo "Downloading wiki-100k most used terms..."
    wget -O data/wiki-100k.txt https://gist.githubusercontent.com/h3xx/1976236/raw/bbabb412261386673eff521dddbe1dc815373b1d/wiki-100k.txt
fi

if [ ! -f data/glove.6B.zip ]; then
    echo "Downloading GloVe 6B parameters, pretrained model."
    wget -O data/glove.6B.zip https://nlp.stanford.edu/data/wordvecs/glove.6B.zip
    echo "Unzupping GloVe pretrained model."
    unzip -q data/glove.6B.zip -d data/
fi

if [ ! -f data/entailData.txt ]; then
    echo "Downloading initial text corpora for training."

    #TODO: Find out -- where was the original entailData.txt retrieved from?

    # Initial test corpora: The Adventures of Sherlock Holmes
    wget -O data/entailData.txt https://www.gutenberg.org/files/1661/1661-0.txt
fi

CONDA_ENVS=$(conda env list | awk '{print $1}')
if ! [[ $CONDA_ENVS = *"text-generator"* ]]; then
    echo "Creating conda text-generator environment."
    conda env create -f environment.yml
fi

conda activate text-generator

if [ ! -f data/glove_model.txt ]; then
    echo "Translating GloVe into Word2Vec"
    python -m gensim.scripts.glove2word2vec --input  data/glove.6B.50d.txt --output data/glove_model.txt
fi