> # Deprecated! ⚠️
> Mercury has been deprecated in favor of [Magnesium Oxide](https://github.com/magnesium-uploader/magnesium-oxide), its successor! 
> 
> No support will be given here and we **highly encourage** you to check out Magnesium Oxide!

# Mercury

A lightning fast private ShareX uploader coded in Python using FastAPI.

## Warning

Mercury is not ready for production use!

Some features are not implemented yet, such as setting the uploader's domain as well as support for multiple domains.

This is a work in progress.

## Features

- Fast and easy to use API with JSON and Swagger (OpenAPI)
- Encrypted uploads with Fernet encryption (AES-128-CBC)
- Hash checking to ensure uploads are not tampered with

## Installation

**⚠️ The following installation steps have not been fully tested, and should be treated with caution...**

The following installation steps are crafted for Ubuntu 20.04 LTS.

```bash
# Install Python3.10
sudo apt-add-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.10 python3.10-distutils

# Install pip
curl https://bootstrap.pypa.io/get-pip.py | sudo python3.10

# Create a user for Mercury that we can switch to later
sudo adduser mercury
su - mercury # Switch to the new user

# Clone the repository
git clone https://github.com/ChecksumDev/Mercury.git /home/mercury/server
cd /home/mercury/server

# Install dependencies
python3.10 -m pip install -r requirements.txt

# Configure mercury
cp ext/config.py.example src/config.py
nano src/config.py # Edit the config file

# Return to the original user
exit

# Daemonize the server using systemd
sudo cp ext/mercury.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mercury
sudo systemctl start mercury
```

## Contributing

Contributions are welcome! Please open a PR with any changes you'd like to make.

Please ensure your contribution is in accordance with the [Contributing Guidelines](https://github.com/ChecksumDev/Mercury/blob/main/CONTRIBUTING.md).

## License

Mercury is licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.html).
