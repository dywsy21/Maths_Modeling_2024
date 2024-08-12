Basic annotations:
    /    represents the root directory, the top of the file hierarchy
    ~    represents the home directory, eg. /home/username
    .    represents the current directory
    ..   represents the parent directory

Common operations:
    cd [path]    change directory  eg. cd /home/username
    pwd          print working directory
    ls           list files and directories of current directory
    mkdir [dir]  make directory
    touch [file] create file
    cp [source] [destination]  copy file or directory
    mv [source] [destination]  move file or directory
    rm [file]    remove file, often used with -r to remove directory recursively
    cat [file]   print file content
    vim [file]   edit file with vim
    grep [pattern] [file]  search for pattern in file
    chmod [permissions] [file]  change file permissions, just use chmod 777 [file] to give all permissions

Every time you need a specific command but shows command not found, try
sudo apt install [package] to install the package containing the command.
