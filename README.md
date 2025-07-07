# Google Photos Background Switcher

Since Google removed virtually all the useful functionality from the Google Photos API, tools like John's Background
Switcher and rclone no longer work with Google Photos. This program is intended as a workaround to automatically rotate
your desktop background through the photos in a Google Photos album. It works by opening the URL of an album in a
headless browser and downloading a random photo from the Google Photos web app.

## Limitations

Currently, this script only works on Windows.

## Usage

This script requires a Firefox profile in which you are logged into your Google Photos account. If you already have a
Firefox profile that you use for other purposes, you will want to create a new profile specifically for this script.

1. Ensure you have Firefox installed.
2. Open Firefox and create a new profile, if needed.
3. Navigate to https://photos.google.com/ and follow the prompts to log in.
4. Locate your Firefox profile directory. It should look something like "C:\Users\\{your
   username}\AppData\Roaming\Mozilla\Firefox\Profiles\\{profile ID}{.default or .default-release}"
5. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

6. Run the script:
   ```
   usage: google-photos-background-switcher.py [-h] --firefox-profile FIREFOX_PROFILE --album-url ALBUM_URL
                                
   Set random Google Photos album image as wallpaper.
   
   options:
     -h, --help            show this help message and exit
     --firefox-profile FIREFOX_PROFILE
                           Path to the Firefox profile directory
     --album-url ALBUM_URL
                           URL of the Google Photos album
   ```

### As a Scheduled Tasks

Practically speaking, this script is most useful as a scheduled task. For instance, you might want it to switch your
background once a day. To run the script as a scheduled task at midnight every day, complete the following steps:

1. Build the script into an executable with PyInstaller:

    ```
   pyinstaller google-photos-background-switcher.py --distpath . --onefile --noconsole
   ```

2. Using an Administrator PowerShell session in the root of this repository, Create a scheduled task, replacing
   `{path to your Firefox profile}` and `{URL of the Google Photos album}` with the appropriate values:

   ```
   $Action = New-ScheduledTaskAction `
    -Execute "$((Get-Location).Path)\google-photos-background-switcher.exe" `
    -Argument "--firefox-profile {path to your Firefox profile} --album-url {URL of the Google Photos album}" `
    -WorkingDirectory "$((Get-Location).Path)"

   $Trigger = New-ScheduledTaskTrigger -Daily -At "12:00AM"
   
   $Settings = New-ScheduledTaskSettingsSet `
   -AllowStartIfOnBatteries `
   -DontStopIfGoingOnBatteries `
   -StartWhenAvailable `
   -MultipleInstances IgnoreNew `
   -NetworkId Any
   
   Register-ScheduledTask `
   -TaskName GooglePhotosBackgroundSwitcher `
   -Action $Action `
   -Trigger $Trigger `
   -Settings $Settings `
   -RunLevel Highest `
   -User $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
   ```
