# Linux Basics (from roadmap.sh)

Source: https://roadmap.sh/linux

## File System Structure
```
/           # Root
├── bin/        # Essential binaries
├── boot/       # Boot loader files
├── dev/        # Device files
├── etc/        # Configuration files
├── home/       # User home directories
├── lib/        # Libraries
├── opt/        # Optional software
├── proc/       # Process info
├── root/       # Root user's home
├── sbin/       # System binaries
├── tmp/        # Temporary files
├── usr/        # User programs
└── var/        # Variable data (logs, etc.)
```

## Essential Commands

### File Operations
| Command | Purpose |
|---------|----------|
| `ls -la` | List files (detailed) |
| `cd <dir>` | Change directory |
| `pwd` | Print working directory |
| `cp src dest` | Copy files |
| `mv src dest` | Move/rename files |
| `rm <file>` | Remove files |
| `mkdir <dir>` | Create directory |
| `rm -rf <dir>` | Remove directory (recursive, force) |
| `touch <file>` | Create empty file |

### File Viewing
| Command | Purpose |
|---------|----------|
| `cat <file>` | Display file contents |
| `less <file>` | Paginated view |
| `head -n 10 <file>` | First 10 lines |
| `tail -n 10 <file>` | Last 10 lines |
| `tail -f <file>` | Follow log file |

### Permissions
```bash
chmod 755 script.sh    # rwxr-xr-x
chmod u+x script.sh     # Add execute for user
chown user:group file  # Change owner/group
sudo command            # Run as superuser
```

**Permission bits**: `r=4, w=2, x=1`
- `755` = user: rwx, group: r-x, others: r-x

## Process Management
| Command | Purpose |
|---------|----------|
| `ps aux` | List all processes |
| `top` / `htop` | Interactive process viewer |
| `kill <pid>` | Terminate process |
| `kill -9 <pid>` | Force kill |
| `bg` | Background a job |
| `fg` | Foreground a job |
| `jobs` | List background jobs |

## Package Management

### Debian/Ubuntu (apt)
```bash
sudo apt update              # Update package list
sudo apt install <pkg>      # Install package
sudo apt remove <pkg>       # Remove package
sudo apt upgrade            # Upgrade all packages
```

### RHEL/CentOS (yum/dnf)
```bash
sudo yum install <pkg>       # Install package
sudo dnf install <pkg>      # Newer systems
```

## Useful Utilities
| Command | Purpose |
|---------|----------|
| `grep "text" file` | Search text in file |
| `find / -name "*.py"` | Find files by pattern |
| `tar -czf archive.tar.gz dir/` | Compress |
| `curl -O <url>` | Download file |
| `wget <url>` | Download file (alternative) |
| `ssh user@host` | SSH to remote |
| `scp file user@host:/path` | Copy to remote |
| `df -h` | Disk usage |
| `du -sh *` | Directory sizes |
| `free -h` | Memory usage |

## Shell Scripting Basics
```bash
#!/bin/bash
# Variables
NAME="World"
echo "Hello $NAME"

# Conditionals
if [ -f "file.txt" ]; then
    echo "File exists"
else
    echo "File not found"
fi

# Loops
for file in *.txt; do
    echo "Processing $file"
done
```

## Networking
| Command | Purpose |
|---------|----------|
| `ip addr` | Show IP addresses |
| `ping <host>` | Test connectivity |
| `netstat -tuln` | List listening ports |
| `ss -tuln` | Modern netstat |
| `curl ifconfig.me` | Get public IP |
| `iptables` | Firewall rules |

## Best Practices
- **Use `sudo` sparingly**: Only when needed
- **Check before `rm -rf`**: Double-check paths
- **Use `grep` with pipes**: Chain commands for power
- **Learn vim/nano**: At least basics for editing
- **Understand permissions**: Security matters
- **Read man pages**: `man <command>` for help
