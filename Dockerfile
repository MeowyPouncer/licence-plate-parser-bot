FROM python:3.8
RUN apt-get update && apt-get install -y \
    gcc \
    libglib2.0-0 \
    libgl1-mesa-glx \
    python3-dev \
    git \
    libturbojpeg0 \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y gnupg wget curl unzip --no-install-recommends; \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | \
    gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/google.gpg --import; \
    chmod 644 /etc/apt/trusted.gpg.d/google.gpg; \
    echo "deb https://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list; \
    apt-get update -y; \
    apt-get install -y google-chrome-stable;

RUN CHROMEDRIVER_VERSION=$(curl https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE); \
    wget -N https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip -P ~/ && \
    unzip ~/chromedriver-linux64.zip -d ~/ && \
    rm ~/chromedriver-linux64.zip && \
    mv -f ~/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    rm -rf ~/chromedriver-linux64

RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxi6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libcups2 \
    libxkbcommon0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt
COPY . .
RUN chmod +x /app/run_every_second.sh
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
