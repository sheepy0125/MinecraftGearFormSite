# Setup ===========================================================================================

# Import
import flask
import flask_sqlalchemy
import datetime
import random
import requests
import json
from productDictionary import *

# Get settings
with open ("Settings.json") as settings_json_file:
    settings_dictionary = json.load(settings_json_file)

    DATABASE_NAME =     settings_dictionary["database_name"]
    SECRET_KEY =        settings_dictionary["secret_key"]
    WEBHOOK_URL =       settings_dictionary["webhook_url"]
    WEBSITE_DOMAIN =    settings_dictionary["website_domain"]

# Setup website
main_website = flask.Flask(__name__, template_folder = "template")
main_website.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_NAME}"
main_website.config["JSON_SORT_KEYS"] = False
main_database = flask_sqlalchemy.SQLAlchemy(main_website)
main_website.secret_key = SECRET_KEY

# Classes =========================================================================================

# Form order class
class FormOrders(main_database.Model):
    # Setup
    id = main_database.Column(main_database.Integer, primary_key = True)
    name = main_database.Column(main_database.String(20), nullable = False)
    content = main_database.Column(main_database.PickleType, nullable = False)
    date_created = main_database.Column(main_database.DateTime, nullable = False)
    pin = main_database.Column(main_database.String(20), nullable = False)
    priority = main_database.Column(main_database.Boolean, nullable = False)
    status = main_database.Column(main_database.String(20), nullable = False)

# Misc. functions =================================================================================

# Get diamonds to stacks
def get_diamonds_to_stacks(amount_of_diamonds):
    order_cost = f"{int(amount_of_diamonds / 64)} stacks {amount_of_diamonds % 64} diamonds"
    return order_cost

# Make sure order is valid
def check_if_order_is_valid(order):
    if order is not None: return True
    else: flask.flash(f"Order ID {id} is not valid.")
    return flask.redirect("/viewAllOrders")

# Check password
def check_password():
    with open ("password.txt") as real_password_text:
        real_password_text = real_password_text.readlines()
        decrypted_password = ""
        
        # Get the encrypted password
        character_count = 0

        for character in real_password_text[0]:
            character_ascii_num = ord(character)

            if character_count % int(real_password_text[3]) != 0:
                character_ascii_num += int(real_password_text[1])
            else:
                character_ascii_num += int(real_password_text[2])

            if character_ascii_num > 32: decrypted_password += str(chr(character_ascii_num) + real_password_text[4])
            else: decrypted_password += str(character_count)

    return decrypted_password

# Check if the order can be edited
def order_can_be_edited(order):
    if order.status == "Recieved": return True
    else: flask.flash("This order is not allowed to be edited at this time.")
    return False
        

# Error handling ==================================================================================

# Page not found
@main_website.errorhandler(404)
def page_not_found(error):
    return flask.render_template("pageNotFound.html"), 404

# Internal server error
@main_website.errorhandler(500)
def internal_server_error(error):
    return flask.render_template("internalServerError.html"), 500

# Pages ===========================================================================================

# Index page
@main_website.route("/")
def index():
    return flask.render_template("index.html")

# Blank page
@main_website.route("/blank")
def blank():
    return flask.render_template("blank.html")

# List of enchants page 
@main_website.route("/allEnchantments")
def all_enchants():
    return flask.render_template("allEnchantments.html", enchantDictionary = enchant_dictionary)

# Form related pages ==============================================================================

# Form and submissions
@main_website.route("/form", methods = ["POST", "GET"])
def form():
    # Clicked button
    if flask.request.method == "POST":
        # If editing
        editing_bool = True if flask.request.form["action"] == "Re-submit order!" else False

        # If submitting editing
        if flask.request.form["action"] == "Submit order!" or editing_bool:
            # Get all data
            order_content = flask.request.form
            order_username = flask.request.form["Username"]

            # Make data look pretty
            order_content_dict = {}
            order_content_dict["Extra"] = {}
            ordered_products = []

            # Get all products
            for product_name in product_dictionary.keys():
                # Iterate through each field in order content
                for order_attribute in order_content.items():
                    # Get value for field
                    value_for_attribute = order_attribute[1]

                    # If the name is in the current field
                    if product_name in order_attribute[0]:
                        # Make it show just enchantment and enchant number
                        order_product = product_name
                        for character in order_attribute[0]:
                            if character.isnumeric():
                                order_product += f" {character}"
                                break

                        # Initialize the product if it hasn't been
                        if order_product not in ordered_products:
                            order_content_dict[order_product] = {}
                            ordered_products.append(order_product)
                            enchant_list = []

                        attribute = order_attribute[0].replace(order_product, "")

                        if "Multiple Choice" in attribute:
                            attribute = value_for_attribute

                        if (not "Name" in attribute) and (not "Additional" in attribute):
                            enchant_list.append(attribute[1::]) if attribute.startswith(" ") else enchant_list.append(attribute)
                            order_content_dict[order_product]["Enchantments"] = enchant_list

                        else:
                            order_content_dict[order_product][attribute] = value_for_attribute

            # Additional information
            order_content_dict["Extra"]["Additional Information"] = order_content["Additional Information"]
            # Minecraft server
            order_content_dict["Extra"]["Minecraft Server"] = order_content["Minecraft Server"]

            order_price = 5

            # Get the product name (from "Sword 1" to "Sword")
            for product_ordered in ordered_products:
                product_ordered = product_ordered.replace(" ", "")
                for character in product_ordered:
                    if character.isnumeric():
                        product_ordered = product_ordered.strip(character)

                order_price += product_dictionary[product_ordered]["productCost"]

            order_content_dict["Extra"]["Estimated Cost"] = get_diamonds_to_stacks(order_price)

            # Get random 4 digit PIN
            if not editing_bool: random_pin = str(random.randint(0, 9999)).zfill(4)
            
            # Prioritize?
            if "Priority" in flask.request.form:
                order_priority = True
                order_price += 10

            else: order_priority = False

            # Submit
            if not editing_bool:
                form_submission = FormOrders(name = order_username, content = order_content_dict, pin = random_pin, date_created = datetime.datetime.utcnow(), priority = order_priority, status = "Recieved")

                # Save to database
                try:
                    main_database.session.add(form_submission)
                    main_database.session.commit()

                # Error happened
                except Exception:
                    flask.flash("There was a problem with submitting your order! Please contact Pink_Sheepy.")
                    return flask.redirect("/")

                flask.flash(f"Your order (#{form_submission.id}) has been recieved!")
                flask.flash(f"Your estimated total cost is {get_diamonds_to_stacks(order_price)}. Please go to Sheepy's base to drop off payment.")
                flask.flash(f"Your order PIN for editing and deleting your order is {random_pin}")

                # Send webhook
                message = f"```Date ordered (GMT): {form_submission.date_created}\nPrioritize: {order_priority}\nEstimated cost: {order_content_dict['Extra']['Estimated Cost']}```\nClick [here]({WEBSITE_DOMAIN}/viewOrder/{form_submission.id}) to view the order.\n<@!246795601709105153>"
                
                
                embed = {}
                embed["title"] = f"New Order from {order_username} (#{form_submission.id})!"
                embed["description"] = message
                embed["color"] = 0xd74894

                data_to_send = {}
                data_to_send["username"] = "God Gear Website Alert System"
                data_to_send["embeds"] = []
                data_to_send["embeds"].append(embed)

                result = requests.post(WEBHOOK_URL, json = data_to_send, headers = {"Content-Type": "application/json"})

                try:
                    result.raise_for_status()
                except requests.exceptions.HTTPError as error:
                    print(f"Error occured! {error}")
                else:
                    print(f"Payload delivered successfully, code {result.status_code}.")

            # Edit
            else:
                form_id = flask.request.form["FormID"]
                order = FormOrders.query.filter_by(id = form_id).first()

                # Make sure order can be edited
                if order_can_be_edited(order):
                    # Update row
                    try:
                        order.name = order_username
                        order.content = order_content_dict
                        order.priority = order_priority
                        order.date_created = datetime.datetime.utcnow()
                        main_database.session.commit()

                    # Error happened
                    except Exception:
                        flask.flash("There was a problem with editing your order! Please contact Pink_Sheepy.")
                        return flask.redirect("/")

                    flask.flash(f"Your order (#{form_id}) has been re-submitted!")
                    flask.flash(f"Your estimated total cost is {get_diamonds_to_stacks(order_price)}. Please go to Sheepy's base to drop off payment.")

                # Order cannot be edited
                else:
                    return flask.redirect("/viewAllOrders")

            return flask.redirect("/")

        # Still on first page
        else:
            order_content = {}
            for product in product_dictionary.items():
                order_content[product[0]] = int(flask.request.form[product[1]["variableName"]])

            # Going to next page
            if flask.request.form["action"] == "Next page":
                return flask.render_template("formEnchants.html", order_content = order_content, product_dictionary = product_dictionary)

            # Just getting price
            elif flask.request.form["action"] == "Estimated cost":
                order_cost = 5

                for ordered_product in order_content.items():
                    order_cost += int(ordered_product[1]) * int(product_dictionary[ordered_product[0]]["productCost"])

                flask.flash(f"Estimated total cost is {get_diamonds_to_stacks(order_cost)}.")
                return flask.redirect("/blank")

    # Not submitting
    else:
        order = FormOrders.query.order_by(FormOrders.date_created).all()
        return flask.render_template("formSelection.html", product_dictionary = product_dictionary, order = order)

# View submissions
@main_website.route("/viewAllOrders")
def view_all_orders():
    all_orders = FormOrders.query.order_by(FormOrders.date_created).all()
    return flask.render_template("viewSubmissions.html", allOrders = all_orders, timedelta = datetime.timedelta)

# Get raw data of order
@main_website.route("/getRawData/<int:id>", methods = ["POST", "GET"])
def get_raw_data(id):
    order = FormOrders.query.get_or_404(id)

    # If password is submitted
    if flask.request.method == "POST":
        # Check password
        password_inputted = flask.request.form["PasswordViewRawData"]
        decrypted_password = check_password()

        # Password matches
        if password_inputted == decrypted_password:
            return {"id": order.id, "name": order.name, "content": order.content, "date_created": order.date_created, "pin": order.pin, "priority": order.priority}

        # Password doesn't match
        else:
            flask.flash(f"Password {password_inputted} is not correct. Nice try.")

    return flask.render_template("getRawDataPasswordScreen.html", order = order)

# View order
@main_website.route("/viewOrder/<int:id>")
def view_order(id):
    order = FormOrders.query.filter_by(id = id).first()

    if check_if_order_is_valid(order):
        # Try to show GUI
        try: return flask.render_template("orderViewGUI.html", order = order, timedelta = datetime.timedelta, product_dictionary = product_dictionary)
        # Failed, so revert to old
        except Exception: flask.flash("There was an error accessing the new view order page.")
        return flask.redirect(f"/viewOrderNoGUI/{id}")

# View order (NO GUI)
@main_website.route("/viewOrderNoGUI/<int:id>")
def view_order_no_gui(id):
    order = FormOrders.query.filter_by(id = id).first()
    if check_if_order_is_valid(order): return flask.render_template("orderView.html", order = order, timedelta = datetime.timedelta)

# Delete order password entered
@main_website.route("/deleteOrder/<int:id>", methods = ["POST", "GET"])
def delete_order(id):
    # If removing
    if flask.request.method == "POST":
        order_to_delete = FormOrders.query.get_or_404(id)

        # Check password
        password_inputted = flask.request.form["PasswordRemove"]

        # Easter egg
        if password_inputted == "LaCraftyIsSmelly!@#$":
            flask.flash("Your password is the truth.")

        decrypted_password = check_password()

        # Password or PIN matches
        pin_matches = True if password_inputted == order_to_delete.pin else False
        if password_inputted == decrypted_password or pin_matches:
            # Make sure if user entered PIN that the order can be edited
            if pin_matches and not order_can_be_edited(order_to_delete):
                return flask.redirect("/viewAllOrders")

            # Attempt to remove
            try:
                main_database.session.delete(order_to_delete)
                main_database.session.commit()
                flask.flash(f"Successfully deleted order {id}")

            # Failed to remove
            except Exception:
                flask.flash(f"There was a problem removing order {id}")

            return flask.redirect("/viewAllOrders")

        # Password doesn't match
        else:
            flask.flash(f"Password {password_inputted} is not correct. Nice try.")

    order = FormOrders.query.filter_by(id = id).first()
    if check_if_order_is_valid(order): return flask.render_template("removeSubmission.html", order = order)

# Edit order
@main_website.route("/editOrder/<int:id>", methods = ["POST", "GET"])
def edit_order(id):
    # Get order
    order = FormOrders.query.filter_by(id = id).first()

    # Make sure order is allowed to be edited
    if order_can_be_edited(order) and check_if_order_is_valid(order):
        # If on password screen (GET request)
        if flask.request.method == "GET": return flask.render_template("editFormPasswordScreen.html", order = order)

        # Submitted PIN
        else: 
            # See if the PIN is correct
            inputted_pin = flask.request.form["OrderPINEdit"]

            if inputted_pin == order.pin: return flask.render_template("editFormEditing.html", order = order, timedelta = datetime.timedelta, product_dictionary = product_dictionary)
            else: flask.flash(f"That pin ({inputted_pin}) is not correct.")
            return flask.redirect(f"/editOrder/{id}")

    # Order cannot be ordered
    else:
        return flask.redirect("/viewAllOrders")

# Change status
@main_website.route("/changeStatus/<int:id>", methods = ["POST", "GET"])
def change_status(id):
    # Get order
    order = FormOrders.query.filter_by(id = id).first()
    check_if_order_is_valid(order)

    # If submitted change
    if flask.request.method == "POST":
        # Get the password and check it
        inputted_password = flask.request.form["PasswordStatusChange"]
        if inputted_password == check_password():            
            # Change status
            try:
                order.status = flask.request.form["status_change"]
                main_database.session.commit()
            
            # Error
            except Exception:
                flask.flash("There was an error changing the status.")
        
        return flask.redirect(f"/viewOrder/{id}")
    
    # If going to submit change
    else:
        return flask.render_template("/changeStatus.html", order = order)

# Run website =====================================================================================
if __name__ == "__main__":
    main_website.run(debug = True)
    # main_website.run(debug = False)
    # main_website.run(host = "0.0.0.0", port = 6969)