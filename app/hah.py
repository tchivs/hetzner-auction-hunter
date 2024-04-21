#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import requests_file
import json
import notifiers
import argparse
import html2text
import base64

# Use TextTable
from texttable import Texttable

# Use SQLite3
import sqlite3

# Define Server Class
class Server:
    def computeOverallResult(self):
        # For every key in the Dictionary compute the logical AND between match and exclude
        for key in self.matchresult:
            # Store in Result
            self.overallresult[key] = self.matchresult[key] and self.excluderesult[key]

    def fitRequirements(self):
        # Compute Overall Result just in case the User forgot to do it
        self.computeOverallResult()

        # If all keys in self.overallresult are true, then it's OK
        return all(self.overallresult)

    def get_disk_description(self):
        disk_descriptors = [
            desc for desc in self.server_raw["description"] if " GB" in desc or " TB" in desc]
        if len(disk_descriptors) == 0:
            disk_description = "%dx %dGB" % (
                self.server_raw["hdd_count"], self.server_raw["hdd_size"])
        else:
            disk_description = ", ".join(disk_descriptors)
        return disk_description

    def has_quick_disk(self):
        nvme_count = len(self.server_raw.get(
            "serverDiskData", []).get("nvme", []))
        sata_count = len(self.server_raw.get(
            "serverDiskData", []).get("sata", []))

        # Store the found value
        self.disk_quick = nvme_count+sata_count > 0

        # Return Value
        return self.disk_quick

    def get_smallest_disk_size(self):
        general_drives = self.disk_map.get("general", [])
        if len(general_drives) > 0:
            smallest_drive = min(general_drives)
        else:
            smallest_drive = -1

        # Store the found value
        self.disk_each_size = smallest_drive

        # Return Value
        return self.disk_each_size

    def __init__(self, server_raw, tax_percent=0):
        self.server_raw = server_raw
        self.tax_percent = tax_percent

        self.id = server_raw.get("id", 0)
        self.datacenter = server_raw.get("datacenter", "UNKNOWN_DATACENTER")
        self.price = server_raw.get("price", 0.0)*(100+self.tax_percent)/100

        self.ram_size = server_raw.get("ram_size", 0)
        self.ram_description = server_raw.get("ram", ["UNKNOWN_RAM"])[0]

        self.cpu_count = server_raw.get("cpu_count", 0)
        self.cpu_description = server_raw.get("cpu", "UNKNOWN_CPU")

        self.disk_count = server_raw.get("hdd_count", 0)
        self.disk_total_size = server_raw.get("hdd_size", 0)
        self.disk_map = server_raw.get(
            "serverDiskData", {"nvme": [], "sata": [], "hdd": [], "general": []})
        self.disk_quick = self.has_quick_disk()
        self.disk_description = self.get_disk_description()

        self.sp_hw_raid = False
        self.sp_red_psu = False
        self.sp_ecc = False
        self.sp_gpu = False
        self.sp_ipv4 = False
        self.sp_inic = False
        for special in server_raw.get("specials", []):
            if special == 'HWR':
                self.sp_hw_raid = True
            if special == 'RPS':
                self.sp_red_psu = True
            if special == 'ECC':
                self.sp_ecc = True
            if special == 'GPU':
                self.sp_gpu = True
            if special == 'IPv4':
                self.sp_ipv4 = True
            if special == 'iNIC':
                self.sp_inic = True
        # interesting fields left: setup_price, fixed_price, next_reduce*, serverDiskData, traffic, bandwidth

        # Copy Field Names to self.match and self.enabled for easier Debugging
        # self.match -> tells if the match has been found
        # self.cmdline -> tells if the command line option setting this Parameter has been passed
        # self.enabled -> tells if the the filtering based on this Parameter is enabled
        #self.cmdline = dict()
        self.matchcriteria = dict()
        self.excludecriteria = dict()
        self.matchresult = dict()
        self.excluderesult = dict()
        self.overallresult = dict()
        for property in self.__dict__:
        #for property in server_raw:
            # Get Property Name
            name = property

            # Exclude self.match itself in order to prevent loops
            # Exclude also other fields that might not be needed
            if (name not in ["matchcriteria" , "excludecriteria" , "matchresult" , "excluderesult" , "overallresult"]) and (name not in ["server_raw"]):
                # By default Criteria is Empty String
                self.matchcriteria[name] = ""
                self.excludecriteria[name] = ""

                # By default all Servers Satisfy the Criteria
                self.matchresult[name] = True
                self.excluderesult[name] = True
                self.overallresult[name] = True

        # Print Dictionary for Debug
        #print(self.cmdline)
        #print(self.enabled)
        #print(self.match)

    def get_url(self):
        return f"https://www.hetzner.com/sb?search={self.id}"

    def get_header(self):
        msg = f"Hetzner server #{self.id} in {self.datacenter} for {self.price}€"
        return msg

    def get_message(self, html=True, verbose=True):
        url = self.get_url()
        msg = f"<b>Hetzner</b> server #{self.id} in {self.datacenter} for {self.price}€: <br />" + \
              f"<b>{self.ram_size}GB RAM, {self.cpu_count}x {self.cpu_description}</b>, {self.disk_description}<br />" + \
              f"<a href='{self.get_url()}'>{url}</a><br />"
        if verbose:
            json_raw = json.dumps(self.server_raw)
            msg += f"<br /><u>Details</u>:<br /><pre>{json_raw}</pre><br />"
        if not html:
            msg = html2text.html2text(msg)
        return msg

    def __repr__(self):
        # Define Properties to Exclude from Print
        excludeProperties = ["server_raw" , "matchcriteria" , "excludecriteria" , "matchresult" , "excluderesult" , "overallresult"]

        # Initialize Table
        t = Texttable()

	# Initialize Variable
        data = []

        # Initialize Variable to Header
        header = ["Property" , "Value" , "Match Criteria" , "Exclude Criteria" , "Match Result" , "Exclude Result" , "Overall Result"]
        #text = "{:>20} {:<10} {:<10}".format("" , "Property", "Value"]

        # Iterate over Properties to find those that need to be printed
        #for property in self.__dict__:

        # Limit the Representation to those keys in self.match (or self.exclude, self.result)
        for property in self.matchcriteria:
            # Name is the same as property
            name = property

            # Check if Property exists in Class
            if property in self.__dict__:
                value = getattr(self, property)
            else:
                value = None

            if name in self.matchcriteria:
                match_criteria = self.matchcriteria[name]
            else:
                match_criteria = None

            if name in self.excludecriteria:
                exclude_criteria = self.excludecriteria[name]
            else:
                exclude_criteria = None

            #if name in self.cmdline:
            #    cmdline_value = self.cmdline[name]
            #else:
            #    cmdline_value = "Undefined"

            if name in self.matchresult:
                match_result = self.matchresult[name]
            else:
                match_result = None

            if name in self.excluderesult:
                exclude_result = self.excluderesult[name]
            else:
                exclude_result = None

            if name in self.overallresult:
                overall_result = self.overallresult[name]
            else:
                overall_result = None


            if name not in excludeProperties:
                #mystr = f"{:<20} {:<10} {:<10}\n"
                #print(f"{name} -> {value}")
                #text += f"{name} -> {value}\n"
                #text += mystr.format("" , name, value)
                data.append([name , value , match_criteria , exclude_criteria , match_result , exclude_result , overall_result])

        # Add the Headers to the Table
        t.add_rows([header] , header=True)

        # Add all the Data to the Table
        t.add_rows(data , header=False)

        # Generate String
        str = t.draw()

        # Return everything indented by a tab
        return '\t'.join(('\n'+str.lstrip()).splitlines(True))



# Define Analyis Class that Extends Server
class Analysis(Server):
    def __init__(self, server_raw , tax_percent=0):
        # Call Parent Class Constructor
        Server.__init__(self, server_raw , tax_percent)



def send_notification(notifier, server, send_payload):
    if notifier == None:
        print(f"DUMMY NOTIFICATION TITLE: "+server.get_header())
        msg = server.get_message(
            html=False, verbose=send_payload).encode("utf-8")
        msg_base64 = base64.b64encode(msg).decode("utf-8")
        print(f"DUMMY NOTIFICATION BODY:  {msg_base64}")
    else:
        html_html = notifier.schema.get("properties").get("html")
        html_pamo = notifier.schema.get("properties").get("parse_mode")
        html_supported = html_html or html_pamo

        title_subject = notifier.schema.get("properties").get("subject")
        title_title = notifier.schema.get("properties").get("title")

        msg = server.get_message(html=html_supported, verbose=send_payload)
        title = server.get_header()

        if html_html:
            if title_subject:
                notifier.notify(message=msg, html=True, subject=title)
            elif title_title:
                notifier.notify(message=msg, html=True, title=title)
            else:
                notifier.notify(message=msg, html=True)
        elif html_pamo:
            if title_subject:
                notifier.notify(message=msg, parse_mode="html", subject=title)
            elif title_title:
                notifier.notify(message=msg, parse_mode="html", title=title)
            else:
                notifier.notify(message=msg, parse_mode="html")
        else:
            if title_subject:
                notifier.notify(message=msg, subject=title)
            elif title_title:
                notifier.notify(message=msg, title=title)
            else:
                notifier.notify(message=msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='hah.py -- checks for newest servers on Hetzner server auction (server-bidding) and pushes to one of dozen providers supported by Notifiers library')

    parser.add_argument('--data-url', dest='data_url' , nargs=1, required=False, type=str,
                        default=[
                            'https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json'],
                        help='URL to live_data_sb.json')

    parser.add_argument('--provider', dest='provider' , nargs=1, required=False, type=str,
                        default=["dummy"],
                        help='Notifiers provider name - see https://notifiers.readthedocs.io/en/latest/providers/index.html')

    parser.add_argument('--tax', dest='tax_percent' , nargs=1, required=False, type=int,
                        default=[19],
                        help='tax rate (VAT) in percents, defaults to 19 (Germany)')

    parser.add_argument('--price', dest='price' , nargs=1, required=False, type=int,
                        help='max price (€)')

    parser.add_argument('--disk-count',  dest='disk_count' , nargs=1, required=False, type=int,
                        default=[1],
                        help='min disk count')

    parser.add_argument('--disk-total-size', dest='disk_total_size' , nargs=1, required=False, type=int,
                        help='min disk capacity in total (GB)')

    parser.add_argument('--disk-each-size', dest='disk_each_size' ,  nargs=1, required=False, type=int,
                        help='min disk capacity per each disk (GB)')

    parser.add_argument('--disk-quick', dest='disk_quick' , action='store_true',
                        help='require SSD/NVMe')

    # Special Properties
    parser.add_argument('--hw-raid', dest='sp_hw_raid' , action='store_true',
                        help='require Hardware RAID')

    parser.add_argument('--red-psu', dest='sp_red_psu' , action='store_true',
                        help='require Redundant PSU')

    parser.add_argument('--ecc', dest='sp_ecc' , action='store_true',
                        help='require ECC memory')

    parser.add_argument('--gpu', dest='sp_gpu' , action='store_true',
                        help='require discrete GPU')

    parser.add_argument('--ipv4', dest='sp_ipv4' , action='store_true',
                        help='require IPv4')

    parser.add_argument('--inic', dest='sp_inic' , action='store_true',
                        help='require Intel NIC')



    parser.add_argument('--cpu-count', dest='cpu_count' , nargs=1, required=False, type=int,
                        default=[1],
                        help='min CPU count')

    parser.add_argument('--match-cpu', dest='match_cpu_description' , nargs=1, required=False, type=str,
                        help='match specific server by CPU description')

    parser.add_argument('--exclude-cpu', dest='exclude_cpu_description' , nargs=1, required=False, type=str,
                        help='exclude specific server by CPU description (has priority over --match-cpu)')

    parser.add_argument('--ram', dest='ram_size' , nargs=1, required=False, type=int,
                        help='min RAM (GB)')

    parser.add_argument('--dc', dest='datacenter' , nargs=1, required=False,
                        help='datacenter (FSN1-DC15) or location (FSN)')

    parser.add_argument('-f', nargs='?',
                        default='/tmp/hah.txt',
                        help='state file')

    parser.add_argument('--exclude-tax', dest='exclude_tax' , action='store_true',
                        help='exclude tax from output price')

    parser.add_argument('--test-mode', dest='test_mode' , action='store_true',
                        help='do not send actual messages and ignore state file')

    parser.add_argument('--debug', dest='debug' , action='store_true',
                        help='debug mode')

    parser.add_argument('--send-payload', dest='send_payload' , action='store_true',
                        help='send server data as JSON payload')

    cli_args = parser.parse_args()


    if not cli_args.test_mode:
        f = open(cli_args.f, 'a+')
        idsProcessed = open(cli_args.f).read()
        if cli_args.provider[0] == "dummy":
            notifier = None
        else:
            notifier = notifiers.get_notifier(cli_args.provider[0])

    servers = None
    try:
        s = requests.Session()
        s.mount('file://', requests_file.FileAdapter())
        rsp = s.get(cli_args.data_url[0], headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15'})
        servers = json.loads(rsp.text)['server']
    except Exception as e:
        print('Failed to download auction list')
        print(e)
        exit(1)

    for server_raw in servers:
        tax = cli_args.tax[0] if not cli_args.exclude_tax else 0.0
        server = Server(server_raw, tax)

        # Debug
        #print(server)

        # Store Command Line Arguments in Server class
        #for key in server.cmdline:
        #    name = key
        #
        #    # If value is also in the list of argparse
        #    if key in cli_args.__dict__:
        #        value = getattr(cli_args , name)
        #        #print(f"Command Line Option: {name} -> {value}")
        #        if isinstance(value , list):
        #            # Get only the first element
        #            value = value[0]
        #
        #        # Only store if the key already exist
        #        if name in server.cmdline:
        #            server.cmdline[name] = value


        # Store Command Line Arguments in Server class
        # Store as either "Match" or "Exclude" depending on the Argument
        for key in cli_args.__dict__:
            # Get Value for this Argument
            value = getattr(cli_args , key)

            # Check for --match or at least no "--exclude"
            if ("match" in key) or ("exclude" not in key):
                # Adapt key name for self.match[key] addressing
                name = key.replace("match_" , "")

                # Only store if the key already exist
                if name in server.matchcriteria:
                    # Add key to match
                    server.matchcriteria[name] = value

            # Check for --exclude
            if ("exclude" in key):
                # Adapt key name for self.match[key] addressing
                name = key.replace("exclude_" , "")
                print(name)
                # Only store if the key already exist
                if name in server.excludecriteria:
                    # Add key to exclude
                    server.excludecriteria[name] = value

                #print(f"Command Line Option: {name} -> {value}")
                #if isinstance(value , list):
                #    # Get only the first element
                #    value = value[0]


        if cli_args.debug:
            print(json.dumps(server_raw))
        if not cli_args.test_mode and str(server.id) in idsProcessed:
            continue

        datacenter_matches = False if cli_args.datacenter else True
        if cli_args.datacenter is not None and cli_args.datacenter[0] in server.datacenter:
            datacenter_matches = True

        # Store result inside Class
        server.matchresult['datacenter'] = datacenter_matches

        price_matches = server.price <= cli_args.price[0] if cli_args.price else True

        # Store result inside Class
        server.matchresult['price'] = price_matches

        cpu_count_matches = server.cpu_count >= cli_args.cpu_count[
            0] if cli_args.cpu_count else True

        # Store result inside Class
        server.matchresult['cpu_count'] = cpu_count_matches

        ram_size_matches = server.ram_size >= cli_args.ram_size[0] if cli_args.ram_size else True

        # Store result inside Class
        server.matchresult['ram_size'] = ram_size_matches

        disk_count_matches = server.disk_count >= cli_args.disk_count[
            0] if cli_args.disk_count else True

        # Store result inside Class
        server.matchresult['disk_count'] = disk_count_matches

        disk_total_size_matches = server.disk_total_size >= cli_args.disk_total_size[
            0] if cli_args.disk_total_size else True
        disk_each_size_matches = server.get_smallest_disk_size(
        ) >= cli_args.disk_each_size[0] if cli_args.disk_each_size else True
        disk_quick_matches = server.has_quick_disk() if cli_args.disk_quick else True

        # Store result inside Class
        server.matchresult['disk_total_size'] = disk_total_size_matches
        server.matchresult['disk_each_size'] = disk_each_size_matches
        server.matchresult['disk_quick'] = disk_quick_matches


        sp_hw_raid_matches = server.sp_hw_raid if cli_args.sp_hw_raid else True

        # Store result inside Class
        server.matchresult['sp_hw_raid'] = sp_hw_raid_matches


        sp_red_psu_matches = server.sp_red_psu if cli_args.sp_red_psu else True

        # Store result inside Class
        server.matchresult['sp_red_psu'] = sp_red_psu_matches


        sp_ecc_matches = server.sp_ecc if cli_args.sp_ecc else True

        # Store result inside Class
        server.matchresult['sp_ecc'] = sp_ecc_matches


        sp_gpu_matches = server.sp_gpu if cli_args.sp_gpu else True

        # Store result inside Class
        server.matchresult['sp_gpu'] = sp_gpu_matches


        sp_ipv4_matches = server.sp_ipv4 if cli_args.sp_ipv4 else True

        # Store result inside Class
        server.matchresult['sp_ipv4'] = sp_ipv4_matches


        sp_inic_matches = server.sp_inic if cli_args.sp_inic else True


        # Store result inside Class
        server.matchresult['sp_inic'] = sp_inic_matches



        # Match Specific CPUs
        # False by default unless Match is found
        cpu_description_matches = False
        if cli_args.match_cpu_description:

            # Split Possible Matches
            # Make sure both the Description and Search Criteria are lowercase in order not to miss any potential Match
            selected_cpu_matches = cli_args.match_cpu_description[0].lower().split(",")

            # Try to see if any Match allowed is found
            for cpu in selected_cpu_matches:
                if cpu in server.cpu_description.lower():
                    # Found match
                    cpu_description_matches = True
                    #print(f"Server {server.id} matches requested CPU <{cli_args.match_cpu[0]}> (Server has CPU {server.cpu_description})")
        else:
            # Not Required
            cpu_description_matches = True


        # Exclude Specific CPUs
        # True by default unless Match is found
        cpu_description_excludes = True
        if cli_args.exclude_cpu_description:
            # Split Possible Matches
            # Make sure both the Description and Search Criteria are lowercase in order not to miss any potential Match
            selected_cpu_exclusions = cli_args.exclude_cpu_description[0].lower().split(",")

            # Try to see if any Match allowed is found
            for cpu in selected_cpu_exclusions:
                if cpu in server.cpu_description.lower():
                    # Found exclusion match
                    cpu_description_matches = False
                    #print(f"Server {server.id} MUST BE EXCLUDED since CPU <{cpu}> is in EXCLUSION LIST ({cli_args.match_cpu[0]}) - Server has CPU {server.cpu_description})")
        else:
            # Not Required
            cpu_description_excludes = True


        # Store result inside Class
        server.matchresult['cpu_description'] = cpu_description_matches
        server.excluderesult['cpu_description'] = cpu_description_excludes

        print(server)

        if cpu_description_matches:
           print(f"Server {server.id} matches CPU Matching Criteria (Server has CPU {server.cpu_description})")
           print(server)

        # Update the Overall Criterials (XXX_matches && XXX_excludes)
        server.computeOverallResult()

        # Check if Server Satisfies all Criteria of Match+Exclude
        if server.fitRequirements():
        #if price_matches and disk_count_matches and disk_total_size_matches and disk_each_size_matches and \
        #        disk_quick_matches and sp_hw_raid_matches and sp_red_psu_matches and cpu_count_matches and \
        #        ram_size_matches and sp_ecc_matches and sp_gpu_matches and sp_ipv4_matches and sp_inic_matches and \
        #        datacenter_matches and cpu_description_matches:

            # Display Server
            print(server)

            #print("TEST")
            #print(server.get_header())
            if not cli_args.test_mode:
                send_notification(notifier, server, cli_args.send_payload)
                f.write(","+str(server.id))

                # Process Server first in the Database
                #print(server)

                # If Server is not Already in the Database with the same Price
                #pass
                #    #send_notification(notifier, server, cli_args.send_payload)
                #    #f.write(","+str(server.id))

    if not cli_args.test_mode:
        f.close()
