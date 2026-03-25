#!/bin/bash

lang="fr"
family="vikidia"
delay_base=3
max_edits=100

green="\e[32m"
red="\e[31m"
yellow="\e[33m"
cyan="\e[36m"
magenta="\e[35m"
reset="\e[0m"

clear

draw_menu() {
    clear
    echo -e "${cyan}"
    echo " __                     __               __  __ ___ "
    echo "|__) _  _  _| _ _      |__)_  _|_ _ .| _|__)/  \ |  "
    echo "|__)(_|| )(_|(-(_||_|)(|  (_)| |_(_|||_)|__)\__/ |  "
    echo -e "${magenta}         Special vikidia fr (Version 1.0) - by bahati11${reset}\n"

    for i in "${!options[@]}"; do
        if [ $i -eq $selected ]; then
            echo -e " ➤ ${green}${options[$i]}${reset}"
        else
            echo "   ${options[$i]}"
        fi
    done
}

options=("Lancer" "Mode test" "Quitter")
selected=0

while true; do
    draw_menu
    read -rsn1 key
    if [[ $key == $'\x1b' ]]; then
        read -rsn2 key
        [[ $key == "[A" ]] && ((selected--))
        [[ $key == "[B" ]] && ((selected++))
    elif [[ $key == "" ]]; then
        break
    fi
    ((selected<0)) && selected=0
    ((selected>2)) && selected=2
done

[ "$selected" = "2" ] && exit

dry_run=0
[ "$selected" = "1" ] && dry_run=1


printf "${cyan}[...] connexion... ${reset}"

user=$(python3 - <<EOF
import pywikibot
site = pywikibot.Site("$lang", "$family")
site.login()
print(site.user() or "")
EOF
)

[ -z "$user" ] && echo -e "${red}erreur${reset}" && exit 1

echo -e "${green}$user${reset}"

bot=$(python3 - <<EOF
import pywikibot
site = pywikibot.Site("$lang", "$family")
site.login()
print("bot" in site.userinfo['groups'])
EOF
)

if [[ "$bot" == "True" ]]; then
    delay=$delay_base
    mode="bot"
else
    delay=15
    mode="safe"
fi

echo -e "${yellow}[Mode] $mode (${delay}s)${reset}\n"

read -p "Categorie/portail : " input
[[ "$input" != *"/"* ]] && echo -e "${red}format invalide${reset}" && exit 1

category=${input%/*}
portal=${input#*/}

mapfile -t pages < <(python3 - <<EOF
import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site("$lang", "$family")
cat = pywikibot.Category(site, "Catégorie:$category")

for p in pagegenerators.CategorizedPageGenerator(cat):
    if p.exists() and not p.isRedirectPage() and p.namespace() == 0:
        print(p.title())
EOF
)

total=${#pages[@]}
[ "$total" -eq 0 ] && echo -e "${red}aucune page${reset}" && exit 1

echo -e "\n${cyan}$total pages${reset}\n"

count=0

for ((i=0;i<total;i++)); do
    page="${pages[$i]}"
    percent=$(( (i+1)*100 / total ))

    printf "\r${cyan}%3d%%${reset} %s" "$percent" "$page"

    result=$(python3 - <<EOF
import pywikibot, re

site = pywikibot.Site("$lang", "$family")
page = pywikibot.Page(site, "$page")

try:
    text = page.get()

    matches = re.findall(r"\{\{\s*portail\s*\|([^}]*)\}\}", text, re.I)

    existing = set()
    for m in matches:
        for p in m.split("|"):
            existing.add(p.strip().lower())

    if "$portal".lower() in existing:
        print("skip")
        exit()

    lines = text.split("\n")
    new_lines = []
    inserted = False

    for line in lines:
        if not inserted and line.strip().startswith("[[Catégorie:"):
            new_lines.append("{{Portail|" + "$portal" + "}}")
            inserted = True
        new_lines.append(line)

    if not inserted:
        new_lines.append("")
        new_lines.append("{{Portail|" + "$portal" + "}}")

    new_text = "\n".join(new_lines)

    if $dry_run == 1:
        print("dry")
    else:
        page.put(new_text, summary="Ajout de [[Portail:$portal]]")
        print("ok")

except:
    print("err")
EOF
)

    case "$result" in
        ok)
            echo -e " ${green}✔${reset}"
            count=$((count+1))
            ;;
        skip)
            echo -e " ${yellow}•${reset}"
            ;;
        dry)
            echo -e " ${cyan}~${reset}"
            ;;
        err)
            echo -e " ${red}✖${reset}"
            ;;
    esac

    [ "$count" -ge "$max_edits" ] && break
    sleep $delay
done

echo -e "\n\n${green} Terminé : $count modifs${reset}"
