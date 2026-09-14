#!/usr/bin/env python3

# Gufw - https://costales.github.io/projects/gufw/
# Copyright (C) 2008-2025 Marcos Alvarez Costales https://costales.github.io
#
# Gufw is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# Gufw is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Gufw; if not, see http://www.gnu.org/licenses for more
# information.

# Run python get.py
# Get the rules from profiles

from pathlib import Path
import configparser

def main() -> None:
    # Modern path resolution with pathlib
    current_dir: Path = Path(__file__).resolve().parent
    profiles_dir: Path = current_dir / '../data/app_profiles'
    output_file: Path = current_dir / 'extra_translations.py'
    
    # Check if the profiles directory exists
    if not profiles_dir.is_dir():
        print(f"Error: The profiles directory does not exist: {profiles_dir}")
        return
    
    all_categories: set[str] = set()
    
    # Open and write to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n\n')
        f.write('import gettext\n')
        f.write('from gettext import gettext as _\n\n')
        f.write('gettext.textdomain("gufw")\n\n\n')
        f.write('def main() -> None:\n')
        
        # Iterate through each profile file in the directory
        for profile_file in profiles_dir.glob('*.*'):
            if not profile_file.is_file():
                continue
                
            config: configparser.ConfigParser = configparser.ConfigParser()
            try:
                config.read(profile_file, encoding='utf-8')
            except Exception as e:
                print(f"Error reading {profile_file.name}: {e}")
                continue
            
            # Iterate through each section (profile) in the INI file
            for section in config.sections():
                title: str = config.get(section, 'title', fallback='').strip()
                description: str = config.get(section, 'description', fallback='').strip()
                ports: str = config.get(section, 'ports', fallback='').strip()
                categories: str = config.get(section, 'categories', fallback='').strip()
                warning: str = config.get(section, 'warning', fallback='').strip()
                
                # Write if all required fields are present
                if title and description and ports and categories:
                    f.write(f'    print(_("{title}"))\n')
                    f.write(f'    print(_("{description}"))\n')
                    
                    if categories not in all_categories:
                        f.write(f'    print(_("{categories}"))\n')
                        all_categories.add(categories)
                        
                    if warning:
                        f.write(f'    print(_("{warning}"))\n')
                        
        # Add static footer translations
        f.write('    print(_("Authentication is required to run the Firewall Configuration"))\n')
        f.write('    print(_("Firewall Configuration"))\n')
        f.write('    print(_("An easy way to configure your firewall"))\n\n\n')

        f.write('if __name__ == "__main__":\n')
        f.write('    main()')

    print(f"Successfully generated: {output_file.name}")

if __name__ == "__main__":
    main()