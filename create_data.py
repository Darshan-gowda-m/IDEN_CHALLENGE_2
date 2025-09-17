# MIT License

# Copyright (c) 2025 Darshan Gowda M

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import random
import string
import time
import os
from playwright.sync_api import sync_playwright, Page, TimeoutError

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def generate_random_name(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def generate_random_email(name, domain="gmail.com"):
    return f"{name}@{domain}"

def safe_click(page, selector, timeout=5000):
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        element.click()
        return True
    except:
        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            element.click(force=True)
            return True
        except:
            try:
                element = page.wait_for_selector(selector, timeout=timeout)
                page.evaluate('(element) => element.click()', element)
                return True
            except:
                return False

def safe_navigate(page, url, selector_to_wait_for, timeout=10000):
    try:
        page.goto(url)
        page.wait_for_selector(selector_to_wait_for, timeout=timeout)
        return True
    except:
        try:
            page.wait_for_timeout(3000)
            return page.query_selector(selector_to_wait_for) is not None
        except:
            return False

def handle_login(page, config):
    print("Navigating to Atlassian login...")
    page.goto("https://admin.atlassian.com")
    
    try:
        page.wait_for_selector('text=Log in', timeout=5000)
        page.click('text=Log in')
        print("Clicked on Log in button")
    except:
        print("No login button found, proceeding directly")
    
    try:
        page.wait_for_selector('input[type="email"]', timeout=10000)
        print("Email field found")
    except:
        print("Email field not found, checking current URL")
        print(f"Current URL: {page.url}")
        return False
    
    page.fill('input[type="email"]', config['email'])
    print("Email filled")
    
    page.click('button:has-text("Continue")')
    print("Clicked Continue")
    
    try:
        page.wait_for_selector('input[type="password"]', timeout=5000)
        print("Password field found")
        
        page.fill('input[type="password"]', config['password'])
        print("Password filled")
        
        page.click('button:has-text("Log in")')
        print("Clicked Log in")
    except:
        print("No password field found, may be already logged in or SSO")
    
    try:
        page.wait_for_url("**/admin.atlassian.com/o/*/overview", timeout=15000)
        print("Successfully redirected to admin portal")
        return True
    except TimeoutError:
        print("Timeout waiting for admin portal redirect")
        print(f"Current URL: {page.url}")
        
        if page.query_selector('button:has-text("Accept all")'):
            page.click('button:has-text("Accept all")')
            print("Accepted terms")
            page.wait_for_url("**/admin.atlassian.com/o/*/overview", timeout=10000)
            return True
        
        if "admin.atlassian.com" in page.url and "/o/" in page.url:
            print("Already on admin page")
            return True
            
        return False

def create_groups(page: Page, account_id: str, num_groups: int, config=None):
    print("Creating groups...")
    
    existing_groups = []
    if os.path.exists('created_groups.json'):
        try:
            with open('created_groups.json', 'r') as f:
                existing_groups = json.load(f)
            print(f"Loaded {len(existing_groups)} existing groups")
        except:
            print("Could not load existing groups, starting fresh")
    
    new_groups = []

    for i in range(num_groups):
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            try:
                group_name = f"group_{generate_random_name(6)}"
                group_desc = f"Description for {group_name}"

                # Navigate to groups page with better waiting
                if not safe_navigate(page, f"https://admin.atlassian.com/o/{account_id}/groups", 'h1:has-text("Groups")'):
                    print("⚠️ Could not navigate to groups page reliably, trying simple navigation")
                    page.goto(f"https://admin.atlassian.com/o/{account_id}/groups")
                    page.wait_for_timeout(3000)

                create_button_selectors = [
                    'button:has-text("Create group")',
                    '[data-testid="create-group-button"]',
                    'button >> text=Create',
                ]

                create_button_found = False
                for selector in create_button_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        page.click(selector, force=True)
                        create_button_found = True
                        print(f"Clicked create group button using selector: {selector}")
                        break
                    except:
                        continue

                if not create_button_found:
                    print("⚠️ Could not find create group button, skipping this group")
                    retry_count += 1
                    continue

                page.wait_for_selector('text=Create group', timeout=5000)
                page.wait_for_timeout(1000)

                name_selectors = [
                    'input[data-testid="group-name-input"]',
                    'input[placeholder*="Group\'s name" i]',
                    'input[name="name"]',
                    'input[type="text"]',
                ]

                name_field = None
                for selector in name_selectors:
                    try:
                        name_field = page.wait_for_selector(selector, timeout=3000)
                        if name_field:
                            break
                    except:
                        continue

                if not name_field:
                    print("❌ Could not find group name field")
                    retry_count += 1
                    continue

                name_field.fill(group_name)
                page.keyboard.press("Tab")
                print(f"Filled group name: {group_name}")

                try:
                    desc_field = page.wait_for_selector('textarea', timeout=3000)
                    desc_field.fill(group_desc)
                    print("Filled group description")
                except:
                    print("⚠️ No description field found, continuing...")

                page.wait_for_timeout(1000)

                try:
                    selector = 'button[data-testid="test-create-group-modal-button"]:not([disabled])'
                    page.wait_for_selector(selector, timeout=5000)
                    page.locator(selector).click()
                    print("✅ Clicked enabled Create button")
                except Exception as e:
                    print(f"❌ Create button never became enabled: {e}")
                    retry_count += 1
                    continue

                try:
                    page.wait_for_timeout(2000)
                    page.wait_for_selector(f'text="{group_name}"', timeout=5000)
                    group_id = f"group_{i}_{int(time.time())}"
                    new_groups.append({"id": group_id, "name": group_name, "description": group_desc})
                    print(f"✅ Created group {i+1}/{num_groups}: {group_name}")
                    break  # Success, break out of retry loop
                except:
                    print(f"⚠️ Group {group_name} may not have been created")
                    retry_count += 1
                    continue

            except TimeoutError as e:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"❌ Failed to create group after {max_retries} retries: {e}")
                    break
                print(f"⚠️ Timeout occurred, retrying ({retry_count}/{max_retries})...")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"❌ Unexpected error creating group: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    break
                page.wait_for_timeout(2000)

        page.wait_for_timeout(1000)

    all_groups = existing_groups + new_groups
    
    with open('created_groups.json', 'w') as f:
        json.dump(all_groups, f, indent=2)
    
    print(f"Saved {len(all_groups)} total groups to created_groups.json")
    
    return all_groups

def create_users(page, account_id, num_users, domain, groups, users_per_group, config):
    print("Creating users...")
    
    existing_users = []
    if os.path.exists('created_users.json'):
        try:
            with open('created_users.json', 'r') as f:
                existing_users = json.load(f)
            print(f"Loaded {len(existing_users)} existing users")
        except:
            print("Could not load existing users, starting fresh")
    
    new_users = []
    success_count = 0  # Tracks only successful invites

    while success_count < num_users:  # Keep trying until we reach desired count
        user_name = f"user_{generate_random_name(8)}"
        user_email = generate_random_email(user_name, domain)

        try:
            # Navigate to users page
            if not safe_navigate(page, f"https://admin.atlassian.com/o/{account_id}/users", 'h1:has-text("Users")'):
                page.goto(f"https://admin.atlassian.com/o/{account_id}/users")
                page.wait_for_timeout(3000)

            # Open invite modal
            invite_selectors = [
                'button:has-text("Invite users")',
                'button:has-text("Invite user")',
                '[data-testid="invite-users-button"]'
            ]
            for selector in invite_selectors:
                if page.query_selector(selector):
                    page.click(selector)
                    print(f"Clicked invite button: {selector}")
                    break
            else:
                print("❌ Invite button not found")
                continue

            page.wait_for_selector('text=Email addresses', timeout=10000)
            print("Invite modal loaded")

            # Fill email first
            email_selectors = [
                'textarea[placeholder*="email"]',
                'input[placeholder*="email"]',
                'textarea',
                'input[type="email"]'
            ]
            email_filled = False
            for selector in email_selectors:
                if page.query_selector(selector):
                    page.fill(selector, user_email)
                    print(f"Filled email with selector: {selector}")
                    email_filled = True
                    break
            if not email_filled:
                print("❌ Email input not found")
                continue

            page.wait_for_timeout(1000)

            # Expand advanced options (groups)
            view_more_button = page.query_selector('button:has-text("View more options")')
            if view_more_button:
                view_more_button.click()
                print("Clicked 'View more options'")
                page.wait_for_timeout(800)

            # Select groups
            selected_groups = []
            if groups and users_per_group > 0:
                selected_groups = random.sample(groups, min(users_per_group, len(groups)))
                print(f"Attempting to select groups: {[g['name'] for g in selected_groups]}")

                group_input_selectors = [
                    'input[aria-label*="group"]',
                    'input[placeholder*="group"]',
                    '#group-membership-input',
                    'input[data-testid*="group"]',
                    'div[class*="select"] input'
                ]

                group_input = None
                for selector in group_input_selectors:
                    group_input = page.query_selector(selector)
                    if group_input:
                        break
                if not group_input:
                    group_section = page.query_selector('div:has-text("Group membership")')
                    if group_section:
                        group_input = group_section.query_selector('input')

                if not group_input:
                    print("⚠️ Could not find group input field, skipping group selection")
                    selected_groups = []
                else:
                    for idx, group in enumerate(selected_groups):
                        try:
                            group_input.click()
                            page.wait_for_timeout(300)

                            if idx == 0:
                                page.keyboard.press('Control+A')
                                page.keyboard.press('Backspace')

                            group_input.type(group["name"], delay=100)
                            page.wait_for_timeout(800)

                            option_selectors = [
                                f'div[role="option"]:has-text("{group["name"]}")',
                                f'div[class*="option"]:has-text("{group["name"]}")',
                                f'li:has-text("{group["name"]}")',
                                f'div:has-text("{group["name"]}")'
                            ]
                            option_found = False
                            for opt_selector in option_selectors:
                                try:
                                    option = page.wait_for_selector(opt_selector, timeout=2000)
                                    if option:
                                        option.click()
                                        print(f"✅ Selected group: {group['name']}")
                                        option_found = True
                                        page.wait_for_timeout(300)
                                        break
                                except:
                                    continue

                            if not option_found:
                                page.keyboard.press("Enter")
                                print(f"✅ Selected group using Enter: {group['name']}")
                                page.wait_for_timeout(500)

                        except Exception as e:
                            print(f"⚠️ Error selecting group {group['name']}: {e}")
                            try:
                                page.keyboard.press("Escape")
                                page.wait_for_timeout(300)
                            except:
                                pass
                            continue

            page.wait_for_timeout(500)

            # Click send button
            send_button_selectors = [
                'button:has-text("Send invite"):not([disabled])',
                '[data-testid="invite-submit-button"]:not([disabled])',
                'button:has-text("Send"):not([disabled])',
                'button[type="submit"]:not([disabled])'
            ]

            send_button = None
            for selector in send_button_selectors:
                send_button = page.query_selector(selector)
                if send_button:
                    is_disabled = page.evaluate('(element) => element.disabled', send_button)
                    if not is_disabled:
                        send_button.click()
                        print("✅ Clicked send invite button")
                        break
            if not send_button:
                print("❌ No enabled send button found")
                page.screenshot(path=f"debug_no_send_button.png")
                continue

            # Wait 1 second after clicking send
            page.wait_for_timeout(1000)

            # Detect failure
            error_found = False
            error_messages = [
                'text="Something went wrong"',
                'text="Try again later"',
                '[role="alert"]:has-text("wrong")',
                '[role="alert"]:has-text("later")'
            ]
            for err in error_messages:
                if page.query_selector(err):
                    print(f"❌ Something went wrong for {user_email}. Retrying...")
                    error_found = True
                    break

            # Only increment success if no error
            if not error_found:
                success_count += 1
                print(f"✅ Successfully invited user {success_count}/{num_users}: {user_email}")
                new_users.append({
                    "email": user_email,
                    "name": user_name,
                    "groups": [g["id"] for g in selected_groups] if selected_groups else []
                })

        except Exception as e:
            print(f"⚠️ Unexpected error during invitation: {e}")
            page.screenshot(path=f"debug_error_user.png")

        # Wait 2 seconds before next attempt
        page.wait_for_timeout(2000)

    # Save all users
    all_users = existing_users + new_users
    with open('created_users.json', 'w') as f:
        json.dump(all_users, f, indent=2)
    print(f"Saved {len(all_users)} total users to created_users.json")
    
    return all_users

def main():
    config = load_config()
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=config['headless'], slow_mo=config['slow_mo'])
            context = browser.new_context()
            page = context.new_page()
            
            # Set longer default timeouts
            page.set_default_timeout(15000)
            
            if not handle_login(page, config):
                print("Login failed. Please check your credentials and try again.")
                browser.close()
                return
            
            account_id = page.url.split("/o/")[1].split("/")[0]
            print(f"Account ID: {account_id}")
            
            groups = create_groups(page, account_id, config['num_groups'], config)
            
            users = create_users(
                page, account_id, config['num_users'], 
                config['domain'], groups, config['users_per_group'], config
            )
            
            print("Data creation completed!")
            print(f"Total: {len(groups)} groups and {len(users)} users")
            
        except Exception as e:
            print(f"❌ Critical error: {e}")
            # Take screenshot for debugging
            page.screenshot(path="error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    main()