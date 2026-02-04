from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

class RPAService:
    def __init__(self):
        # We define options here but instantiate the driver in the specific method
        # to ensure a fresh browser session for every request.
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("detach", True)

    def apply_for_scheme(self, user_data, scheme_name="generic"):
        """
        ROUTER: Decides which bot to launch based on the scheme name.
        """
        print(f"🤖 RPA Request Received for: {scheme_name}")
        
        # Normalize scheme name safely
        scheme_key = str(scheme_name).lower()
        
        if "pan" in scheme_key or "permanent account" in scheme_key:
            return self._apply_for_pan(user_data)
        elif "scholarship" in scheme_key:
            return {"status": "skipped", "message": "Scholarship automation is currently in development."}
        else:
            return {"status": "error", "message": f"No automation script found for '{scheme_name}'"}

    def _apply_for_pan(self, user_data):
        """
        YOUR ROBUST PAN BOT (Protean/NSDL)
        """
        print("🤖 RPA: Launching PAN Bot with Advanced Logic...")
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        except Exception as e:
            return {"status": "error", "message": f"Driver Init Failed: {str(e)}"}

        missing_fields = []

        try:
            # 1. EXTRACT DATA
            personal = user_data.get("personal_details", {})
            contact = user_data.get("contact_details", {})

            fname = personal.get("first_name", "")
            mname = personal.get("middle_name", "")
            # Default to "." if last name is missing (common requirement hack)
            lname = personal.get("last_name") if personal.get("last_name") else "." 
            dob   = personal.get("dob", "")
            mobile = contact.get("mobile", "")
            email = contact.get("email", "")
            
            print(f"   -> Data: {fname} {lname} | DOB: {dob} | Mob: {mobile}")

            # 2. NAVIGATE
            url = "https://onlineservices.proteantech.in/paam/endUserRegisterContact.html"
            driver.get(url)
            wait = WebDriverWait(driver, 20)

            # 3. DROPDOWNS (Application Type, Category, Title)
            try:
                # Wait for dropdowns to appear
                dropdowns = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
                if len(dropdowns) >= 3:
                    # Application Type -> New PAN (Index 1)
                    Select(dropdowns[0]).select_by_index(1)
                    time.sleep(1) # Small pause for UI refresh
                    
                    # Refresh element references
                    dropdowns = driver.find_elements(By.TAG_NAME, "select")
                    
                    # Category -> Individual (Index 1)
                    Select(dropdowns[1]).select_by_index(1)
                    
                    # Title -> Shri/Mr (Index 1) - Logic can be improved with Gender later
                    Select(dropdowns[2]).select_by_index(1)
            except Exception as e:
                print(f"⚠️ Dropdown Error: {e}")

            # 4. NAMES
            print(f"   -> Filling Name: {fname} {lname}")
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if len(text_inputs) >= 2:
                # Index 0 is often Last Name/Surname
                text_inputs[0].send_keys(lname)
                # Index 1 is often First Name
                text_inputs[1].send_keys(fname)
                # Index 2 is Middle Name
                if mname and len(text_inputs) > 2:
                    text_inputs[2].send_keys(mname)

            # 5. DOB (YOUR ROBUST FIX)
            if dob:
                print(f"   -> Attempting DOB: {dob}")
                try:
                    # Try finding by ID then XPath
                    try:
                        dob_input = driver.find_element(By.ID, "dob")
                    except:
                        dob_input = driver.find_element(By.XPATH, "//input[@type='date' or contains(@name, 'dob')]")

                    # ACTION 1: Unlock readonly
                    driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)

                    # ACTION 2: Type
                    dob_input.click()
                    dob_input.clear()
                    dob_input.send_keys(dob) 
                    time.sleep(0.5)

                    # ACTION 3: Close Datepicker Popup
                    dob_input.send_keys(Keys.TAB)

                    # ACTION 4: Verify & Force if needed
                    current_val = dob_input.get_attribute("value")
                    if current_val != dob:
                        print(f"⚠️ Typing failed (Got '{current_val}'). Forcing via JS...")
                        driver.execute_script(f"arguments[0].value = '{dob}';", dob_input)

                except Exception as e:
                    print(f"⚠️ DOB Error: {e}")
                    missing_fields.append("Date of Birth")
            else:
                missing_fields.append("Date of Birth")

            # 6. EMAIL
            if email:
                try:
                    # Usually ID is 'emailId' on Protean
                    email_input = driver.find_element(By.ID, "emailId")
                    email_input.send_keys(email)
                except:
                    # Fallback
                    try:
                        email_input = driver.find_element(By.XPATH, "//input[contains(@name, 'email') or contains(@id, 'email')]")
                        email_input.send_keys(email)
                    except:
                        missing_fields.append("Email ID")
            else:
                missing_fields.append("Email ID")

            # 7. MOBILE
            if mobile:
                print(f"   -> Filling Mobile: {mobile}")
                try:
                    # Using the robust XPath
                    mob_input = driver.find_element(By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mobile number')]/following::input[1]")
                    mob_input.clear()
                    mob_input.send_keys(mobile)
                except:
                    print("⚠️ Could not locate Mobile field")
                    missing_fields.append("Mobile Number")
            else:
                missing_fields.append("Mobile Number")

            # 8. CHECKBOX (Consent)
            try:
                driver.execute_script("document.querySelector('input[type=\"checkbox\"]').click();")
            except:
                pass

            # 9. REPORT STATUS
            if missing_fields:
                msg = f"Opened with partial data. Missing: {', '.join(missing_fields)}."
                return {"status": "partial_success", "message": msg, "missing": missing_fields}
            else:
                return {"status": "success", "message": "Form opened and pre-filled successfully!"}

        except Exception as e:
            print(f"❌ RPA Runtime Error: {e}")
            return {"status": "error", "message": str(e)}