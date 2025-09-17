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
import time
import re
from playwright.sync_api import sync_playwright, Page, TimeoutError

def load_config():
    """Load configuration from config.json file"""
    with open('config.json', 'r') as f:
        return json.load(f)

def save_json(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved data to {filename}")

def handle_login(page, config):
    """Handle the complete login process with proper redirects"""
    print("Navigating to Atlassian login...")
    page.goto("https://admin.atlassian.com")
    
    # Wait for and click the login button if present
    try:
        page.wait_for_selector('text=Log in', timeout=5000)
        page.click('text=Log in')
        print("Clicked on Log in button")
    except:
        print("No login button found, proceeding directly")
    
    # Wait for email field - could be on id.atlassian.com or admin.atlassian.com
    try:
        page.wait_for_selector('input[type="email"]', timeout=10000)
        print("Email field found")
    except:
        print("Email field not found, checking current URL")
        print(f"Current URL: {page.url}")
        return False
    
    # Fill email
    page.fill('input[type="email"]', config['email'])
    print("Email filled")
    
    # Click continue
    page.click('button:has-text("Continue")')
    print("Clicked Continue")
    
    # Wait for password field or redirect
    try:
        page.wait_for_selector('input[type="password"]', timeout=5000)
        print("Password field found")
        
        # Fill password
        page.fill('input[type="password"]', config['password'])
        print("Password filled")
        
        # Click login
        page.click('button:has-text("Log in")')
        print("Clicked Log in")
    except:
        print("No password field found, may be already logged in or SSO")
    
    # Wait for redirect to admin portal
    try:
        page.wait_for_url("**/admin.atlassian.com/o/*/overview", timeout=15000)
        print("Successfully redirected to admin portal")
        return True
    except TimeoutError:
        print("Timeout waiting for admin portal redirect")
        print(f"Current URL: {page.url}")
        
        # Check if we're on a consent page or need to accept terms
        if page.query_selector('button:has-text("Accept all")'):
            page.click('button:has-text("Accept all")')
            print("Accepted terms")
            page.wait_for_url("**/admin.atlassian.com/o/*/overview", timeout=10000)
            return True
        
        # Check if we're already on a admin page
        if "admin.atlassian.com" in page.url and "/o/" in page.url:
            print("Already on admin page")
            return True
            
        return False

def extract_account_id(page):
    """Extract account ID from the current URL"""
    try:
        account_id = page.url.split("/o/")[1].split("/")[0]
        print(f"Account ID: {account_id}")
        return account_id
    except IndexError:
        print("Could not extract account ID from URL")
        return None

def fetch_users_via_api(page, account_id):
    """Fetch users data via the discovered API endpoint with proper cursor-based pagination"""
    print("Fetching users via API...")
    
    users = []
    cursor = None
    base_url = f"https://admin.atlassian.com/gateway/api/admin/v2/orgs/{account_id}/directories/-/users"
    has_more = True
    page_count = 0
    
    while has_more:
        page_count += 1
        print(f"=== Page {page_count} ===")
        
        # Build the URL with cursor if available
        if cursor:
            users_url = f"{base_url}?cursor={cursor}&count=100"
            print(f"Using cursor: {cursor[:50]}...")  # Show first 50 chars of cursor
        else:
            users_url = f"{base_url}?count=100"
            print("Using initial request (no cursor)")
        
        try:
            response = page.evaluate("""async ([url]) => {
                const response = await fetch(url, {
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return await response.json();
            }""", [users_url])
            
            print(f"API Response keys: {list(response.keys())}")
            
            if 'data' in response:
                current_users = response['data']
                users.extend(current_users)
                print(f"Fetched {len(current_users)} users, total: {len(users)}")
                
                # Check for next page cursor
                if 'links' in response and 'next' in response['links'] and response['links']['next']:
                    cursor = response['links']['next']
                    print(f"Next cursor available, continuing...")
                else:
                    # No more pages, exit the loop
                    has_more = False
                    print("No more pages found - stopping pagination")
                    break
            else:
                print(f"Unexpected response format: {response}")
                has_more = False
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error fetching users: {e}")
            has_more = False
    
    print(f"Total users fetched: {len(users)} across {page_count} pages")
    return users

def fetch_groups_via_api(page, account_id):
    """Fetch groups data via the discovered API endpoint with pagination"""
    print("Fetching groups via API...")
    
    groups = []
    start_index = 1
    count = 100
    has_more = True
    
    while has_more:
        groups_url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{account_id}/groups?count={count}&start-index={start_index}"
        
        try:
            response = page.evaluate("""async ([url]) => {
                const response = await fetch(url, {
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });
                return await response.json();
            }""", [groups_url])
            
            if 'groups' in response:
                groups.extend(response['groups'])
                print(f"Fetched {len(response['groups'])} groups, total: {len(groups)}")
                
                if len(response['groups']) < count:
                    has_more = False
                else:
                    start_index += count
            else:
                has_more = False
                
        except Exception as e:
            print(f"Error fetching groups: {e}")
            has_more = False
    
    print(f"Total groups fetched: {len(groups)}")
    return groups

def fetch_last_active_dates(page, account_id, user_ids):
    """Fetch last active dates for users using bulk API"""
    print("Fetching last active dates...")
    
    batch_size = 50
    last_active_data = {}
    
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        batch_ids = [{'accountId': user_id} for user_id in batch]
        
        last_active_url = f"https://admin.atlassian.com/gateway/api/admin/v1/orgs/{account_id}/users/last-active-date-bulk"
        
        try:
            response = page.evaluate("""async ([url, batchData]) => {
                const response = await fetch(url, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(batchData)
                });
                return await response.json();
            }""", [last_active_url, batch_ids])
            
            if 'data' in response:
                for item in response['data']:
                    if 'accountId' in item and 'lastActiveTimestamp' in item:
                        last_active_data[item['accountId']] = item['lastActiveTimestamp']
            
        except Exception as e:
            print(f"Error fetching last active dates for batch: {e}")
    
    return last_active_data

def extract_group_memberships_ui(page, account_id, groups_data):
    """Extract group memberships by visiting each group page and scraping UI"""
    print("Extracting group memberships from UI...")
    
    memberships_data = []
    admin_user_id = "712020:961d02d1-08d0-4a82-a327-bacb754a95ff"  # The problematic admin user to exclude
    
    for group in groups_data:
        group_id = group.get('id')
        group_name = group.get('name', '')
        
        if not group_id:
            continue
            
        print(f"Extracting members for group: {group_name}")
        
        # Navigate to the group details page
        group_url = f"https://admin.atlassian.com/o/{account_id}/groups/{group_id}"
        page.goto(group_url)
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        member_ids = []
        
        # Method 1: Look for user account IDs in the page content
        try:
            # Get the page content and look for user IDs
            content = page.content()
            
            # Look for user IDs in data attributes
            user_id_matches = re.findall(r'data-account-id="([^"]+)"', content)
            member_ids.extend(user_id_matches)
            
            # Look for user IDs in links
            user_link_matches = re.findall(r'/users/([^"/]+)', content)
            member_ids.extend(user_link_matches)
            
            # Remove duplicates and empty values
            member_ids = list(set([uid for uid in member_ids if uid and len(uid) > 10]))
            
            # Filter out the admin user
            member_ids = [uid for uid in member_ids if uid != admin_user_id]
            
        except Exception as e:
            print(f"Error extracting members from page content: {e}")
        
        # Method 2: Look for member elements in the UI
        if not member_ids:
            try:
                member_rows = page.query_selector_all('tr[data-testid], [data-testid*="user"], [data-testid*="member"]')
                for row in member_rows:
                    try:
                        user_id = row.get_attribute('data-account-id') or row.get_attribute('data-user-id')
                        if user_id and user_id != admin_user_id:
                            member_ids.append(user_id)
                    except:
                        continue
            except Exception as e:
                print(f"Error extracting members from UI elements: {e}")
        
        # Remove any duplicates that might have been added
        member_ids = list(set(member_ids))
        
        print(f"Found {len(member_ids)} members for group {group_name}")
        
        memberships_data.append({
            'groupId': group_id,
            'memberIds': member_ids
        })
        
        # Go back to avoid too many page loads
        page.go_back()
        page.wait_for_load_state('networkidle')
        time.sleep(1)
    
    return memberships_data

def parse_users_data(users_data, memberships_data, last_active_data):
    """Parse users data into the required format"""
    parsed_users = []
    
    for user in users_data:
        user_id = user.get('accountId')
        name = user.get('displayName', '')
        email = user.get('email', '')
        
        status = user.get('status', 'unknown')
        if 'accountStatus' in user:
            status = user['accountStatus']
        
        last_active = last_active_data.get(user_id)
        
        user_groups = []
        for membership in memberships_data:
            if user_id in membership['memberIds']:
                user_groups.append(membership['groupId'])
        
        parsed_users.append({
            'id': user_id,
            'name': name,
            'email': email,
            'last_active': last_active,
            'status': status,
            'groups': user_groups
        })
    
    return parsed_users

def parse_groups_data(groups_data, memberships_data):
    """Parse groups data into the required format"""
    parsed_groups = []
    
    for group in groups_data:
        group_id = group.get('id')
        name = group.get('name', '')
        description = group.get('description', '')
        
        group_members = []
        for membership in memberships_data:
            if membership['groupId'] == group_id:
                group_members = membership['memberIds']
                break
        
        parsed_groups.append({
            'id': group_id,
            'name': name,
            'description': description,
            'members': group_members
        })
    
    return parsed_groups

def main():
    """Main function to execute the extraction process"""
    config = load_config()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.get('headless', False))
        context = browser.new_context()
        page = context.new_page()
        
        # Handle login
        if not handle_login(page, config):
            print("Login failed. Please check your credentials and try again.")
            browser.close()
            return
        
        # Extract account ID
        account_id = extract_account_id(page)
        if not account_id:
            print("Could not extract account ID. Exiting.")
            browser.close()
            return
        
        print("=" * 50)
        print("FETCHING DATA")
        print("=" * 50)
        
        # Fetch users
        users_data = fetch_users_via_api(page, account_id)
        
        # Fetch groups
        groups_data = fetch_groups_via_api(page, account_id)
        
        # Fetch last active dates for users
        user_ids = [user.get('accountId') for user in users_data if user.get('accountId')]
        last_active_data = fetch_last_active_dates(page, account_id, user_ids)
        
        # Extract group memberships using UI method (since API method is failing)
        memberships_data = extract_group_memberships_ui(page, account_id, groups_data)
        
        # Parse the data into the required format
        print("=" * 50)
        print("PARSING DATA")
        print("=" * 50)
        
        parsed_users = parse_users_data(users_data, memberships_data, last_active_data)
        parsed_groups = parse_groups_data(groups_data, memberships_data)
        
        # Save to JSON files
        save_json(parsed_users, 'users.json')
        save_json(parsed_groups, 'groups.json')
        
        # Print summary
        print("=" * 50)
        print("EXTRACTION COMPLETE")
        print("=" * 50)
        print(f"Total users extracted: {len(parsed_users)}")
        print(f"Total groups extracted: {len(parsed_groups)}")
        
        total_memberships = sum(len(group['members']) for group in parsed_groups)
        print(f"Total group memberships: {total_memberships}")
        
        browser.close()

if __name__ == "__main__":
    main()
    