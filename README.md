Usage example 1:

```
!git clone https://github.com/rezamarzban/clone-all
%cd clone-all
!python github-clone-all.py --clone-user rezamarzban
!zip -r github_backup.zip .
from google.colab import drive
drive.mount('/content/drive')
```
Then:
```
!cp github_backup.zip /content/drive/MyDrive
```
