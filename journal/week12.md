# Week 12 — Modern APIs
















## Save the work on its own branch named "week-12"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-12
```
<hr/>

## Commit
Add the changes and create a commit named: "Modern APIs"
```sh
git add .
git commit -m "Modern APIs"
```
Push your changes to the branch
```sh
git push origin week-12
```
<hr/>

### Tag the commit
```sh
git tag -a week-12 -m "Modern APIs"
```
<hr/>

### Push your tags
```sh
git push --tags
```
<hr/>

### Switching Between Branches back to Main
```sh
git checkout main
```
<hr/>

### Merge Changes
```sh
git merge week-12
```
<hr/>

### Push Changes to Main
```sh
git push origin main
```
<hr/>

#### Branches?
If you want to keep the "week-1" branch for future reference or additional work, 
you can keep it as is. If you no longer need the branch, you can delete it after merging.
```sh
git branch -d week-12  # Deletes the local branch
git push origin --delete week-12  # Deletes the remote branch
```