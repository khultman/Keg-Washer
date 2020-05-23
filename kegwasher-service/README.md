# KegWasher

## Install

```bash
git clone https://github.com/khultman/Keg-Washer.git
cd kegwasher-service
sudo python3 setup.py install

sudo cp kegwasher.service /etc/systemd/system
sudo systemctl enable kegwasher.service
sudo systemctl start kegwasher.service

```