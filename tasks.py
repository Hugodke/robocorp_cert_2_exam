from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    browser.configure(
            slowmo=100,
        )

    open_robot_order_website()
    close_annoying_modal()
    orders = get_orders()
    for order in orders:
        order_number = fill_the_form(order)
        pdf_file = store_receipt_as_pdf(order_number)
        screenshot = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot, pdf_file)
        order_new_robot()
        close_annoying_modal()
        
    archive_receipts()



def open_robot_order_website():
    """Navigate to the robot ordering portal"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    """Get a csv with the orders from a download link"""
    orders = HTTP().download(url='https://robotsparebinindustries.com/orders.csv', overwrite=True)
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Ordernumber", "Head", "Body", "Legs", "Address"]
    )
    return orders

def close_annoying_modal():
    """Close annoying popup whenever it comes up"""
    page = browser.page()
    page.click("button:text('Yep')")

def fill_the_form(order):
    """Fill the form to create a robot"""
    page = browser.page()
    page.select_option("#head", str(order['Head']))
    page.locator(f"#id-body-{str(order['Body'])}").click()
    page.locator("[placeholder='Enter the part number for the legs']").fill(str(order['Legs']))
    page.fill("#address", order['Address'])
    page.click("button:text('Preview')")
    page.click("button:text('Order')")
    
    while page.locator("[class='alert alert-danger']").is_visible:
        try:
            page.click("#order", timeout=1000)
        except Exception:
            break

    order_number = page.locator("[class='badge badge-success']").text_content()
    return order_number

def store_receipt_as_pdf(order_number):
    """Store the receipt as an PDF file in the output of the task"""
    path = f"output/receipts/order_{order_number}.pdf"
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, path)
    return path

def screenshot_robot(order_number):
    """Take a screenshot of the robot and save it as output"""
    path = f"output/screenshots/order_{order_number}.png"
    page = browser.page()
    element = page.locator("#robot-preview-image")
    element.screenshot(path=path)
    return path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Combines the receipt and the screenshot to one PDF document"""
    pdf = PDF()
    pdf.add_files_to_pdf(files=[screenshot],append=True,target_document=pdf_file)
    
def order_new_robot():
    """Click the button to order another robot"""
    page = browser.page()
    page.click("#order-another")


def archive_receipts():
    "Archive all the combined receipts"
    archive = Archive()
    archive.archive_folder_with_zip("output/receipts", "output/receipts.zip")