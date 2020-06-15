# unity-git-hooks
This repository is intended as a collection of useful git hooks for Unity projects. The following sections detail each hook.

## pre-commit
Before Git prompts the user for a commit message, this hook verifies that each asset has a corresponding meta file in version 
control. The hook will check either the staging area (index) or the existing tracked files to ensure consistency. Specifically,
this can prevent the following situations:
- An asset is newly added without the corresponding meta file
- An asset is newly added such that one or more of its parent directories' meta files are not added
- A meta file is added without the corresponding asset
- An asset is removed without removing the corresponding meta file
- A metafile is removed without removing the corresponding asset
- An asset is moved without also moving the corresponding meta file

### TODO
- One or more newly added assets have clashing guids in their meta files
