# hetzner-auction-hunter

**unofficially** checks for newest servers on Hetzner server auction (server-bidding) and pushes to one of dozen providers supported by [Notifiers library](https://pypi.org/project/notifiers/), including Pushover, SimplePush, Slack, Gmail, Email (SMTP), Telegram, Gitter, Pushbullet, Join, Zulip, Twilio, Pagerduty, Mailgun, PopcornNotify, StatusPage.io, iCloud, VictorOps (Splunk)

[Hetzner Auction website](https://www.hetzner.com/sb)

[![Docker Pulls](https://img.shields.io/docker/pulls/danielskowronski/hetzner-auction-hunter)](https://hub.docker.com/repository/docker/danielskowronski/hetzner-auction-hunter)

The price displayed on hetzner.com by default includes monthly rate for IPv4 address, therefore it's slightly higher than one reported by this tool. You can disable it by toggling *Enable IPv6 only* switch available on top of the list (on hetzner.com). 

## requirements

* python3
* properly configured [Notifiers provider](https://notifiers.readthedocs.io/en/latest/providers/index.html)
* some writable file to store processed offers (defaults to `/tmp/hah.txt`)

## Get Started
```
# Clone Reponsitory
git clone https://github.com/luckylinux/hetzner-auction-hunter.git

# Copy Example .env Configuration
cp .env.example .env

# Edit Environment Variables with your preferred Text Editor
nano .env

# Define what you want to search for
cp search.sh.example search.sh

# Edit search Criteria
nano search.ch

# Build & Upload to local Registry Server ("HACK" for Docker/Podman Compose to pick up the locally built Image)
./build.sh
./upload.sh

# Setup Systemd Service & Timer to automatically perform Search
mkdir -p $HOME/.config/systemd/user
cp hetzner-auction-hunter-runner.service $HOME/.config/systemd/user/
cp hetzner-auction-hunter-runner.timer $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable hetzner-auction-hunter-runner.service
systemctl --user enable hetzner-auction-hunter-runner.timer
systemctl --user restart hetzner-auction-hunter-runner.timer

# Check that everything works
# You should see some output (without errors) in the Systemd Logs
systemctl --user status hetzner-auction-hunter-runner.service
journalctl --user -xeu hetzner-auction-hunter-runner.service

```

## usage

```
usage: hah.py [-h] [--data-url DATA_URL] [--provider PROVIDER] [--tax TAX] [--price PRICE] [--id IDS] [--disk-general-count DISK_GENERAL_COUNT] [--disk-general-total-size DISK_GENERAL_TOTAL_SIZE] [--disk-general-each-size DISK_GENERAL_EACH_SIZE] [--disk-quick] [--disk-quick-count DISK_QUICK_COUNT] [--disk-quick-total-size DISK_QUICK_TOTAL_SIZE] [--disk-quick-each-size DISK_QUICK_EACH_SIZE] [--disk-hdd] [--disk-hdd-count DISK_HDD_COUNT] [--disk-hdd-total-size DISK_HDD_TOTAL_SIZE] [--disk-hdd-each-size DISK_HDD_EACH_SIZE] [--disk-ssd] [--disk-ssd-count DISK_SSD_COUNT] [--disk-ssd-total-size DISK_SSD_TOTAL_SIZE] [--disk-ssd-each-size DISK_SSD_EACH_SIZE] [--disk-nvme] [--disk-nvme-count DISK_NVME_COUNT] [--disk-nvme-total-size DISK_NVME_TOTAL_SIZE] [--disk-nvme-each-size DISK_NVME_EACH_SIZE] [--hw-raid] [--red-psu] [--gpu] [--ipv4] [--inic]
[--cpu-count CPU_COUNT] [--ram RAM] [--ecc] [--dc DC] [-f [F]] [--exclude-tax] [--test-mode] [--debug] [--quiet] [--verbose] [--send-payload]

hah.py -- checks for newest servers on Hetzner server auction (server-bidding) and pushes to one of dozen providers supported by Notifiers library

options:
  # Program Options
  -f [F]                                                  state file
  -h, --help                                              show this help message and exit
  --data-url DATA_URL                                     URL to live_data_sb.json
  --provider PROVIDER                                     Notifiers provider name - see https://notifiers.readthedocs.io/en/latest/providers/index.html
  --exclude-tax                                           exclude tax from output price
  
  # Operating Mode
  --test-mode                                             do not send actual messages and ignore state file
  --send-payload                                          send server data as JSON payload

  # Output Messages Control
  --debug                                                 Debug Mode (generates even more Output than --verbose)
  --verbose                                               Verbose Mode (generates more Output - Useful for Troubleshooting)
  --quiet                                                 Quiet Mode (suppress most Output)

  # General Server Options
  --cpu-count CPU_COUNT                                   min CPU count (Sockets, not Cores)      
  --match-cpu CPU_LIST                                    match Server based on a comma-separated List of CPUs
  --exclude-cpu CPU_LIST                                  exclude Server based on a comma-separated List of CPUs     
  --ram RAM                                               min RAM amount in GB
  --ecc                                                   require ECC memory
  --dc DC                                                 datacenter (FSN1-DC15) or location (FSN)
  --tax TAX                                               tax rate (VAT) in percent, defaults to 19 (Germany)
  --id                                                    server ID to match against a comma-separated List
  --price PRICE                                           max price in EUR

  # General Disk Options
  --disk-general-count DISK_GENERAL_COUNT                 min disk count (considers only HDD+SSD+NVMe)         
  --disk-general-total-size DISK_GENERAL_TOTAL_SIZE       min total disk capacity in GB (considers only HDD+SSD+NVMe)                
  --disk-general-each-size DISK_GENERAL_EACH_SIZE         min disk capacity per disk in GB (considers only HDD+SSD+NVMe)  

  # Quick (SSD + NVMe) Disk Options
  --disk-quick                                            require SSD/NVMe
  --disk-quick-count DISK_QUICK_COUNT                     min disk count (considers only SSD+NVMe)         
  --disk-quick-total-size DISK_QUICK_TOTAL_SIZE           min total disk capacity in GB (considers only SSD+NVMe)                
  --disk-quick-each-size DISK_QUICK_EACH_SIZE             min disk capacity per disk in GB (considers only SSD+NVMe) 

  # HDD Options
  --disk-hdd                                              require HDD
  --disk-hdd-count DISK_HDD_COUNT                         min disk count (considers only HDD)         
  --disk-hdd-total-size DISK_HDD_TOTAL_SIZE               min total disk capacity in GB (considers only HDD)                
  --disk-hdd-each-size DISK_HDD_EACH_SIZE                 min disk capacity per disk in GB (considers only HDD) 

  # SSD Options
  --disk-ssd                                              require SSD
  --disk-ssd-count DISK_SSD_COUNT                         min disk count (considers only SSD)         
  --disk-ssd-total-size DISK_SSD_TOTAL_SIZE               min total disk capacity in GB (considers only SSD)                
  --disk-ssd-each-size DISK_SSD_EACH_SIZE                 min disk capacity per disk in GB (considers only SSD) 

  # NVME Options
  --disk-nvme                                             require NVME 
  --disk-nvme-count DISK_NVME_COUNT                       min disk count (considers only NVMe)         
  --disk-nvme-total-size DISK_NVME_TOTAL_SIZE             min total disk capacity in GB (considers only NVMe)                
  --disk-nvme-each-size DISK_NVME_EACH_SIZE               min disk capacity per disk in GB (considers only NVMe) 

  # Special Options for the Server
  --hw-raid                                               require Hardware RAID
  --red-psu                                               require Redundant PSU
  --gpu                                                   require discrete GPU
  --ipv4                                                  require IPv4
  --inic                                                  require Intel NIC

```

Since there are way too many combinations of providers and their parameters to support as CLI args, you must pass `--provider PROVIDER` as defined on [Notifiers providers list](https://notifiers.readthedocs.io/en/latest/providers/index.html) and export all relevant ENV variables as per [Notifiers usage guide](https://notifiers.readthedocs.io/en/latest/usage.html?highlight=NOTIFIERS_#environment-variables). 

### directly on machine

You'll probably want to put it in crontab and make sure that state file is on permanent storage (`/tmp/` may or may not survive reboot).

#### prepare local env

```bash
pyenv activate
python3 -m pip install -r requirements.txt
```

#### export ENV variables

Those are just examples. Check out https://notifiers.readthedocs.io/en/latest/providers/index.html

For **Pushover**: [register](https://pushover.net/signup), get your User Key from [main page](https://pushover.net) and then [register app](https://pushover.net/apps/build) for which you'll get app token. Then export as follows:

```bash
export NOTIFIERS_PUSHOVER_USER=...
export NOTIFIERS_PUSHOVER_TOKEN=...
export HAH_PROVIDER=pushover
```

For **Gmail**: register, [enable 2FA](https://myaccount.google.com/signinoptions/two-step-verification/enroll-welcome) (required bacuse Google enforces app passwords for non-OAuth clients and you can't have app password without 2FA), [create app password](https://myaccount.google.com/apppasswords) selecting Mail as service. Then export as follows:

```bash
export NOTIFIERS_GMAIL_USERNAME="...@gmail.com" # username
export NOTIFIERS_GMAIL_PASSWORD="..." # app password
export NOTIFIERS_GMAIL_FROM="$NOTIFIERS_GMAIL_USERNAME <$NOTIFIERS_GMAIL_USERNAME>" # optional From field, recommended to use real account email
export NOTIFIERS_GMAIL_TO="..." # recipient
export HAH_PROVIDER=gmail
```

For **Telegram** (discouraged, but provided for legacy compatibility): talk to [@BotFather](https://t.me/BotFather) to create new bot and obtain token, talk to [@myidbot](https://t.me/myidbot) to get your personal chat ID. Then export as follows: 

```bash
export NOTIFIERS_TELEGRAM_TOKEN="...:..."
export NOTIFIERS_TELEGRAM_CHAT_ID="..." 
export HAH_PROVIDER=telegram
```

#### run

To get servers cheaper than 38 EUR with more than 24GB of RAM, disks at least 3TB:

```bash
./hah.py --provider $HAH_PROVIDER --price 38 --disk-size 3000 --ram 24
```

### docker

Example run for Pushover:

```bash
docker build . -t hetzner-auction-hunter:latest --no-cache=true

docker run --rm \
  -v /tmp/hah:/tmp/ \
  -e NOTIFIERS_PUSHOVER_USER=$NOTIFIERS_PUSHOVER_USER \
  -e NOTIFIERS_PUSHOVER_TOKEN=$NOTIFIERS_PUSHOVER_TOKEN \
  hetzner-auction-hunter:latest --provider $HAH_PROVIDER --price 40 --disk-size 3000 --ram 24
```

For more universal executions, you may consider using `docker run --env-file`.

## debugging

```bash
curl https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json | jq > live_data_sb.json
./hah.py --data-url "file:///${PWD}/live_data_sb.json" --debug ...
```

## docker image for hub.docker.com

```bash
hadolint Dockerfile
export TAG=danielskowronski/hetzner-auction-hunter:v...
docker build . -t $TAG --no-cache=true
docker push $TAG
```
