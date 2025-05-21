sudo apt-get update
sudo apt-get upgrade
sudo apt install python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
git pull https://github.com/robdnh/slack-ragbot.git
cd slack-ragbot/slackbot
pip3 install -r requirements.txt