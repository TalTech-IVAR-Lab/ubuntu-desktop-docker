#!/usr/bin/env bash

# A script for the quick setup of Zsh shell with Prezto, several useful plugins and an awesome theme.
#
# Based on https://github.com/gustavohellwig/gh-zsh


#--------------------------------------------------
# Parse CLI options (logic based on https://github.com/ryanoasis/nerd-fonts/blob/master/install.sh)
#--------------------------------------------------
optspec=":f-:"
while getopts "$optspec" optchar; do
  case "${optchar}" in

    # Short options
    f) WITH_FONT=true;;

    -)
      case "${OPTARG}" in
        # Long options
        font) WITH_FONT=true;;
      esac;;

    *)
      echo "Unknown option -${OPTARG}" >&2
      exit 1
      ;;

  esac
done
shift $((OPTIND-1))


#--------------------------------------------------
# Shell Configurations
#--------------------------------------------------
OS="$(uname)"
if [[ "$OS" == "Linux" ]] || [[ "$OS" == "Darwin" ]] ; then
    echo
    if [[ "$OS" == "Linux" ]]; then
        echo "--> Please, type your password (to 'sudo apt install' the requirements):"
        sudo apt update -y
        sudo apt install -y zsh bat git
        echo -e "\nInstalling zsh, bat and git"
    fi
    if [[ "$OS" == "Darwin" ]]; then
        # Inspired by https://github.com/Homebrew/brew
        version_gt() {
        [[ "${1%.*}" -gt "${2%.*}" ]] || [[ "${1%.*}" -eq "${2%.*}" && "${1#*.}" -gt "${2#*.}" ]]
        }
        version_ge() {
        [[ "${1%.*}" -gt "${2%.*}" ]] || [[ "${1%.*}" -eq "${2%.*}" && "${1#*.}" -ge "${2#*.}" ]]
        }
        major_minor() {
        echo "${1%%.*}.$(x="${1#*.}"; echo "${x%%.*}")"
        }
        macos_version="$(major_minor "$(/usr/bin/sw_vers -productVersion)")"
        should_install_command_line_tools() {
        if version_gt "$macos_version" "10.13"; then
            ! [[ -e "/Library/Developer/CommandLineTools/usr/bin/git" ]]
        else
            ! [[ -e "/Library/Developer/CommandLineTools/usr/bin/git" ]] ||
            ! [[ -e "/usr/include/iconv.h" ]]
        fi
        }
        if should_install_command_line_tools && version_ge "$macos_version" "10.13"; then
            echo "--> When prompted for the password, enter your Mac login password."
            shell_join() {
                local arg
                printf "%s" "$1"
                shift
                for arg in "$@"; do
                    printf " "
                    printf "%s" "${arg// /\ }"
                done
            }
            chomp() {
                printf "%s" "${1/"$'\n'"/}"
            }
            have_sudo_access() {
                local -a args
                if [[ -n "${SUDO_ASKPASS-}" ]]; then
                    args=("-A")
                elif [[ -n "${NONINTERACTIVE-}" ]]; then
                    args=("-n")
                fi
            }
            have_sudo_access() {
                local -a args
                if [[ -n "${SUDO_ASKPASS-}" ]]; then
                    args=("-A")
                elif [[ -n "${NONINTERACTIVE-}" ]]; then
                    args=("-n")
                fi

                if [[ -z "${HAVE_SUDO_ACCESS-}" ]]; then
                    if [[ -n "${args[*]-}" ]]; then
                    SUDO="/usr/bin/sudo ${args[*]}"
                    else
                    SUDO="/usr/bin/sudo"
                    fi
                    if [[ -n "${NONINTERACTIVE-}" ]]; then
                    ${SUDO} -l mkdir &>/dev/null
                    else
                    ${SUDO} -v && ${SUDO} -l mkdir &>/dev/null
                    fi
                    HAVE_SUDO_ACCESS="$?"
                fi

                if [[ -z "${HOMEBREW_ON_LINUX-}" ]] && [[ "$HAVE_SUDO_ACCESS" -ne 0 ]]; then
                    abort "Need sudo access on macOS (e.g. the user $USER needs to be an Administrator)!"
                fi

                return "$HAVE_SUDO_ACCESS"
            }
            execute() {
                if ! "$@"; then
                    abort "$(printf "Failed during: %s" "$(shell_join "$@")")"
                fi
            }
            execute_sudo() {
                local -a args=("$@")
                if have_sudo_access; then
                    if [[ -n "${SUDO_ASKPASS-}" ]]; then
                    args=("-A" "${args[@]}")
                    fi
                    execute "/usr/bin/sudo" "${args[@]}"
                else
                    execute "${args[@]}"
                fi
            }
            TOUCH="/usr/bin/touch"
            clt_placeholder="/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"
            execute_sudo "$TOUCH" "$clt_placeholder"
            clt_label_command="/usr/sbin/softwareupdate -l |
                                grep -B 1 -E 'Command Line Tools' |
                                awk -F'*' '/^ *\\*/ {print \$2}' |
                                sed -e 's/^ *Label: //' -e 's/^ *//' |
                                sort -V |
                                tail -n1"
            clt_label="$(chomp "$(/bin/bash -c "$clt_label_command")")"

            if [[ -n "$clt_label" ]]; then
                printf "Xcode Command Line Tools not found\nInstalling...\n"
                execute_sudo "/usr/sbin/softwareupdate" "-i" "$clt_label" &> /dev/null
                execute_sudo "/bin/rm" "-f" "$clt_placeholder" &> /dev/null
                execute_sudo "/usr/bin/xcode-select" "--switch" "/Library/Developer/CommandLineTools" &> /dev/null
            fi
        fi
        # Inspired by https://github.com/Homebrew/brew
    fi
    echo -e "\nShell Configurations"
    if [[ "$OS" == "Darwin" ]]; then
        chsh -s /bin/zsh &> /dev/null
    fi
    if [[ "$OS" == "Linux" ]]; then
        sudo usermod -s /usr/bin/zsh $(whoami) &> /dev/null
        sudo usermod -s /usr/bin/zsh root &> /dev/null
    fi
    if mv -n ~/.zshrc ~/.zshrc_backup_$(date +"%Y-%m-%d_%H:%M:%S") &> /dev/null; then
        echo -e "\n--> Backing up the current .zshrc config to .zshrc_backup-date"
    fi

    #--------------------------------------------------
    # LSDeluxe
    #--------------------------------------------------
    echo -e "\nInstalling LSDeluxe"
    if [[ "$OS" == "Linux" ]]; then
        curl -sL https://raw.githubusercontent.com/wimpysworld/deb-get/main/deb-get | sudo -E bash -s install deb-get
        sudo deb-get install lsd
    fi
    if [[ "$OS" == "Darwin" ]]; then
        brew install lsd &> /dev/null
    fi

    #--------------------------------------------------
    # Prezto and plugins
    #--------------------------------------------------
    echo -e "\nInstalling Prezto"
    # Install Prezto (by downloading the repo into .zprezto folder in our home directory): https://github.com/sorin-ionescu/prezto
    git clone --recursive https://github.com/sorin-ionescu/prezto.git "${ZDOTDIR:-$HOME}/.zprezto"

    # Create symlinks to link Zsh to Prezto configurations (this will overwrite default Zsh files)
    echo -e "\nCreating Prezto symlinks"
    ln -sf ~/.zprezto/runcoms/zlogin ~/.zlogin
    ln -sf ~/.zprezto/runcoms/zlogout ~/.zlogout
    ln -sf ~/.zprezto/runcoms/zpreztorc ~/.zpreztorc
    ln -sf ~/.zprezto/runcoms/zprofile ~/.zprofile
    ln -sf ~/.zprezto/runcoms/zshenv ~/.zshenv
    ln -sf ~/.zprezto/runcoms/zshrc ~/.zshrc

    # Patch Prezto runcoms
    echo -e "\nPatching Prezto runcoms"
    (cd ~/.zprezto/runcoms/ && curl -O https://raw.githubusercontent.com/JGroxz/presto-prezto/main/zshrc) &> /dev/null
    (cd ~/.zprezto/runcoms/ && curl -O https://raw.githubusercontent.com/JGroxz/presto-prezto/main/zpreztorc) &> /dev/null
    if [[ "$OS" == "Linux" ]]; then
        sudo cp ~/.zshrc /root/
    fi

    # Download zplug
    echo -e "\nDownloading zplug..."
    git clone https://github.com/zplug/zplug ~/.zplug

    echo -e "\nPrezto configuration complete (plugins will be installed on the first shell run)"

    #--------------------------------------------------
    # Theme (Powerlevel10k)
    #--------------------------------------------------
    echo -e "\nDownloading theme configuration"

    if [[ "$WITH_FONT" == true ]]; then
        P10K_CONFIG_FILE=".p10k.nerd-font.zsh"
    else
        P10K_CONFIG_FILE=".p10k.zsh"
    fi

    (cd ~/ && curl -o ".p10k.zsh" "https://raw.githubusercontent.com/JGroxz/presto-prezto/main/${P10K_CONFIG_FILE}") &> /dev/null
    if [[ "$OS" == "Linux" ]]; then
        sudo cp ~/.p10k.zsh /root/
    fi
    echo -e "\nTheme configuration done"

    #--------------------------------------------------
    # Meslo Nerd Font (recommended by the creator of Powerlevel10k theme)
    #--------------------------------------------------
    if [[ "$WITH_FONT" == true ]]; then
        echo
        echo -e "Installing Meslo Nerd Font"

        # Select fonts folder based on the current platform
        if [[ "$OS" == "Linux" ]]; then
            FONTS_FOLDER_PATH=~/.fonts
        fi
        if [[ "$OS" == "Darwin" ]]; then
            FONTS_FOLDER_PATH=~/Library/Fonts
        fi

        # Make sure that the fonts directory exists
        mkdir -p ${FONTS_FOLDER_PATH}

        # Download fonts
        (curl -Lo "${FONTS_FOLDER_PATH}/MesloLGS NF Regular.ttf" "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Regular.ttf") &> /dev/null
        (curl -Lo "${FONTS_FOLDER_PATH}/MesloLGS NF Bold.ttf" "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold.ttf") &> /dev/null
        (curl -Lo "${FONTS_FOLDER_PATH}/MesloLGS NF Italic.ttf" "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Italic.ttf") &> /dev/null
        (curl -Lo "${FONTS_FOLDER_PATH}/MesloLGS NF Bold Italic.ttf" "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold%20Italic.ttf") &> /dev/null

        # Refresh font cache if on Linux
        if [[ "$OS" == "Linux" ]]; then
            echo
            echo -e "Resetting Linux font cache"
            (fc-cache -f -v) &> /dev/null
        fi

        echo -e "\nInstalled the font"
    fi

    #--------------------------------------------------
    # Make Zsh the default shell
    #--------------------------------------------------
    echo -e "\nMaking Zsh the default shell for user '$(whoami)'..."
    PATH_TO_ZSH=$(command -v zsh)
    if [[ $PATH_TO_ZSH ]]; then
        sudo usermod --shell $PATH_TO_ZSH $(whoami)
        echo -e "Default shell for user '$(whoami)' is now set to '$PATH_TO_ZSH'."
    else
        echo "Could not make Zsh the default shell: Zsh could not be found. This means that installation has failed. Please check the logs above to find the issue."
        exit 1
    fi

    echo -e "\nPresto-Prezto configuration complete!\n"

    if [[ "$WITH_FONT" == true ]]; then
        echo
        echo -e "(!) Make sure to enable the new Meslo Nerd Font in your terminal using the instructions from here:\n    https://github.com/romkatv/powerlevel10k#meslo-nerd-font-patched-for-powerlevel10k\n\n"
    fi

    # Inspired by https://github.com/romkatv/zsh4humans/blob/v5/sc/exec-zsh-i
    try_exec_zsh() {
        >'/dev/null' 2>&1 command -v "$1" || 'return' '0'
        <'/dev/null' >'/dev/null' 2>&1 'command' "$1" '-fc' '
        [[ $ZSH_VERSION == (5.<8->*|<6->.*) ]] || return
        exe=${${(M)0:#/*}:-$commands[$0]}
        zmodload -s zsh/terminfo zsh/zselect || [[ $ZSH_PATCHLEVEL == zsh-5.8-0-g77d203f && $exe == */bin/zsh && -e ${exe:h:h}/share/zsh/5.8/scripts/relocate ]]' || 'return' '0'
        'exec' "$@" || 'return'
    }
    exec_zsh() {
        'try_exec_zsh' 'zsh' "$@" || 'return'
        'try_exec_zsh' '/usr/local/bin/zsh' "$@" || 'return'
        'try_exec_zsh' '/bin/zsh' "$@" || 'return'
    }
    'exec_zsh' '-i'
    # Inspired by https://github.com/romkatv/zsh4humans/blob/v5/sc/exec-zsh-i

else
    echo "This script is only supported on macOS and Linux."
    exit 0
fi
