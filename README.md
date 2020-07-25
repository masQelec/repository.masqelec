# Repository Bootstrapper
## _Bootstrap GIT repo for setting up a Kodi repository_

_forked from BartOtten with the additions of:_

- Ignore .idea, .git and __MACOSX folders in addons' subfolders
- Ignore various files like .gitignore, .gitattributes
- Copy changelogs (& rename to version number), icons, fanarts to your repository
- Changed from deprecated md5 module to hashlib

**In summary, it can do the following:**
- Create a repository addon which users can install.
- Create the addons.xml and addon.xml.md5 files.
- ZIP-file your addons with version numbers.
- Copy changelogs and rename with version numbers.
- Copy icons & fanarts, if any.

Tested Python versions: 2.7.12+, 3.6.5
