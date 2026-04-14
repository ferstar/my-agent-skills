# glab Quick Reference Guide

A condensed reference for the most commonly used GitLab CLI commands.

## Authentication

```bash
glab auth login                    # Interactive login
glab auth status                   # Check auth status
echo "token" | glab auth login --stdin  # Login with token
```

Notes:
- Stored `glab` auth is sufficient for most commands.
- `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN`, and `OAUTH_TOKEN` override stored credentials when set.
- `glab auth status` is human-readable output. In `glab 1.91.0` the token line shows `Token found:`. Use it for operator checks, not brittle text parsing.

## Merge Requests

```bash
# Listing
glab mr list                       # All open MRs
glab mr list --assignee=@me        # MRs assigned to me
glab mr list --reviewer=@me        # MRs for me to review

# Creating
glab mr create                     # Interactive creation
glab mr create --title "Fix" --description "Desc"
glab mr create --title "Fix" --description "Closes #123"
glab mr create --draft             # Create draft MR
glab mr create --reviewer=alice,bob

# Viewing & Managing
glab mr view 123                   # View MR #123
glab mr checkout 123               # Checkout MR branch
glab mr approve 123                # Approve MR
glab mr merge 123                  # Merge MR
glab mr note 123 -m "Comment"      # Add comment
glab mr note resolve 3107030349    # Resolve MR discussion by note or discussion ID
glab mr note reopen 3107030349     # Reopen MR discussion by note or discussion ID
```

## Issues

```bash
# Listing
glab issue list                    # Open issues
glab issue list --all              # Open and closed issues
glab issue list --closed           # Closed issues
glab issue list --assignee=@me     # Assigned to me
glab issue list --label=bug        # With label

# `--opened` still appears in 1.91.0 examples, and it is legacy usage.

# Creating & Managing
glab issue create                  # Interactive
glab issue create --title "Bug" --label=bug
glab issue view 456                # View issue
glab issue close 456               # Close issue
glab issue update 456 --unlabel=todo
```

## CI/CD

```bash
# Pipelines
glab ci view                       # Watch pipeline
glab ci list                       # List pipelines
glab ci list --ref main            # List pipelines for a ref / branch
glab ci status                     # Pipeline status
glab ci trace                      # View logs

# Running & Managing
glab ci run                        # Trigger pipeline
glab ci lint                       # Lint .gitlab-ci.yml
glab ci retry <job-id|job-name>    # Retry failed job
glab ci cancel pipeline <id>       # Cancel pipeline
```

## Repository

```bash
glab repo clone org/project        # Clone repository
glab repo view                     # View repo details
glab repo fork                     # Fork repository
```

## API

```bash
glab api projects/:id/merge_requests           # GET request
glab api --method POST projects/:id/issues \
  --field title="Bug"              # POST with data
```

## Common Flags

```bash
--help, -h                         # Show help
--repo, -R owner/repo              # Specify repository
--web, -w                          # Open in browser
--output, -o json                  # JSON output
--verbose                          # Verbose output
```

## Environment Variables

```bash
GITLAB_TOKEN=xxx                   # API token
GITLAB_HOST=gitlab.example.org     # Self-hosted GitLab
```

## Configuration

```bash
glab config get                    # View configuration
glab config set key value          # Set config value
```

## Complete Command List

- `glab alias` - Create command shortcuts
- `glab api` - Make API calls
- `glab auth` - Authentication management
- `glab changelog` - Generate changelogs
- `glab check-update` - Check for updates
- `glab ci` - CI/CD operations
- `glab cluster` - Kubernetes cluster management
- `glab completion` - Shell completion
- `glab config` - Configuration management
- `glab deploy-key` - Deploy key management
- `glab duo` - GitLab Duo AI features
- `glab gpg-key` - GPG key management
- `glab incident` - Incident management
- `glab issue` - Issue tracking
- `glab iteration` - Iteration management
- `glab job` - CI job operations
- `glab label` - Label management
- `glab mcp` - MCP server operations
- `glab milestone` - Milestone management
- `glab mr` - Merge request operations
- `glab opentofu` - OpenTofu integration
- `glab release` - Release management
- `glab repo` - Repository operations
- `glab runner` - Runner management
- `glab runner-controller` - Runner controller management
- `glab schedule` - Pipeline schedule management
- `glab securefile` - Secure file management
- `glab snippet` - Snippet operations
- `glab ssh-key` - SSH key management
- `glab stack` - Stack management
- `glab token` - Access token management
- `glab user` - User operations
- `glab variable` - CI/CD variable management
- `glab version` - Show version
- `glab work-items` - Work item management

## Tips

1. Before using a new `glab` subcommand in the current task, run `glab <command> --help` and trust that over memory
2. Commands auto-detect repository context from git remote
3. Use `-R owner/repo` when outside a repository
4. Most commands have `--web` flag to open in browser
5. Use `--output=json` for scripting
6. Enable completion: `glab completion --shell bash`
7. If you hit `unknown flag`, stop and re-check `glab <command> --help` instead of guessing another flag
