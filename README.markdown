# Daily Update Helper

Ahem... Seems like I'm inventing a wheel with this, but here you go.

This script does several simple things:

- connects to Atlassian Confluence via XML RPC
- retrieves a page
- finds git branch names via some regular expressions
- makes a list of found git branches
- allows user to modify this list in a text editor
- rebases each of that branches from some upstream branch (usually `master`)
- if automatic rebase fails, skips that branch
- otherwise, merges it into upstream branch (usually `master`)
- shows a nice summary
