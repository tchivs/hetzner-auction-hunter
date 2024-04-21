#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import requests_file
import json
import notifiers
import argparse
import html2text
import base64

# Import sys Python Module
import sys

# Import os Python Module
import os

# Use TextTable
from texttable import Texttable

# Use SQLite3
import sqlite3

# Define Server Class
class Server:
    # Exclude Properties from Printing / Analysis
    SERVER_PRINT_EXCLUDE_PROPERTIES = ["server_raw"]

    def computeOverallResult(self):
        # For every key in the Dictionary compute the logical AND between match and exclude
        for key in self.matchresult:
            # Store in Result
            self.overallresult[key] = all([self.matchresult[key] , self.excluderesult[key]])

    def fitRequirements(self):
        # Compute Overall Result just in case the User forgot to do it
        self.computeOverallResult()

        # Using for loop
        # If all keys in self.overallresult are true, then it's OK
        #result = True
        #for key in self.overallresult:
        #    if self.overallresult[key] == False:
        #        result = False

        # Return Result
        return all(self.overallresult.values())

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

        # Count how many Quick Disks are installed
        status = nvme_count+sata_count > 0

        # Return Value
        return status

    def has_hdd_disk(self):
        hdd_count = len(self.server_raw.get(
            "serverDiskData", []).get("hdd", []))

        # Count how many HDD Disks are installed
        status = hdd_count > 0

        # Return Value
        return status

    def has_ssd_disk(self):
        ssd_count = len(self.server_raw.get(
            "serverDiskData", []).get("sata", []))

        # Count how many HDD Disks are installed
        status = ssd_count > 0

        # Return Value
        return status

    def has_nvme_disk(self):
        nvme_count = len(self.server_raw.get(
            "serverDiskData", []).get("nvme", []))

        # Count how many Quick Disks are installed
        status = nvme_count > 0

        # Return Value
        return status

    def get_drive_sizes(self , disk_type = "general"):
        # Each Parameter Must be Calculated Invividually
        # "general" does NOT contain the number of Items Corresponding to each Disk !
        hdd_size = self.disk_map.get("hdd", [])
        ssd_size = self.disk_map.get("sata", [])
        nvme_size = self.disk_map.get("nvme", [])

        # Initialize Variable
        drive_sizes = []

        # !! IMPORTANT !!  affecting the variable (drive_sizes = hdd_size to start with) causes the creation of a Pass-by-Reference Issue
        # We must ALWAYS use .extend() also for the first line of each if/else block, in this way we force a copy.
        # Alternatively initialize disk_sizes in the if/else block as drive_sizes = hdd_size.copy() in the first line of each statement.
        if disk_type == "general":
            drive_sizes = hdd_size.copy()
            drive_sizes.extend(ssd_size)
            drive_sizes.extend(nvme_size)

        elif disk_type == "quick":
            drive_sizes = ssd_size.copy()
            drive_sizes.extend(nvme_size)

        elif disk_type == "hdd":
            drive_sizes.extend(hdd_size)

        elif disk_type == "sata" or disk_type == "ssd":
            drive_sizes.extend(ssd_size)

        elif disk_type == "nvme":
            drive_sizes.extend(nvme_size)

        # Return Value
        return drive_sizes

    def get_disk_count(self , disk_type = "general"):
        # Each Parameter Must be Calculated Invividually
        # "general" does NOT contain the number of Items Corresponding to each Disk !

        # Get Drive Sizes
        drive_sizes = self.get_drive_sizes(disk_type)

        # Return Number of Elements Found
        return len(drive_sizes)

    def get_total_disk_size(self , disk_type = "general"): 
        # Get drive Sizes
        drive_sizes = self.get_drive_sizes(disk_type)

        # Check that there is at least 1 Disk
        if len(drive_sizes) > 0:
            sum_drives = sum(drive_sizes)
        else:
            sum_drives = -1

        # Return Value
        return sum_drives

    def get_smallest_disk_size(self  , disk_type = "general"):
        # Get drive Sizes
        drive_sizes = self.get_drive_sizes(disk_type)

        # Check that there is at least 1 Disk
        if len(drive_sizes) > 0:
            smallest_drive = min(drive_sizes)
        else:
            smallest_drive = -1

        # Return Value
        return smallest_drive

    def __init__(self, server_raw, tax_percent=0):
        self.server_raw = server_raw
        self.tax_percent = tax_percent

        self.id = server_raw.get("id", 0)
        self.datacenter = server_raw.get("datacenter", "UNKNOWN_DATACENTER")

        self.price_net = server_raw.get("price", 0.0)
        self.price_gross = self.price_net*(100+self.tax_percent)/100

        self.price = server_raw.get("price", 0.0)*(100+self.tax_percent)/100

        self.ram_size = server_raw.get("ram_size", 0)
        self.ram_description = server_raw.get("ram", ["UNKNOWN_RAM"])[0]

        self.cpu_count = server_raw.get("cpu_count", 0)
        self.cpu_description = server_raw.get("cpu", "UNKNOWN_CPU")

        # !! IMPORTANT !! Make sure, where self.disk_map is used inside other functions, to NOT inadvertently create a reference link.
        # This would result in the number of disks in self.disk_map to increase dramatically
        self.disk_map = server_raw.get(
            "serverDiskData", {"nvme": [], "sata": [], "hdd": [], "general": []})

        # Store Disk Description
        self.disk_description = self.get_disk_description()
        
        # These Variables keep into account the General (HDD + SSD/NVME) Disk Type
        self.disk_general_count = self.get_disk_count('general')
        self.disk_general_total_size = self.get_total_disk_size('general')
        self.disk_general_each_size = self.get_smallest_disk_size('general')

        # These Variables keep into account only the Quick (SSD/NVME) Disk Type only
        self.disk_quick = self.has_quick_disk()
        self.disk_quick_count = self.get_disk_count('quick')
        self.disk_quick_total_size = self.get_total_disk_size('quick')
        self.disk_quick_each_size = self.get_smallest_disk_size('quick')

        # These Variables keep into account only the HDD Disk Type only
        self.disk_hdd = self.has_hdd_disk()
        self.disk_hdd_count = self.get_disk_count('hdd')
        self.disk_hdd_total_size = self.get_total_disk_size('hdd')
        self.disk_hdd_each_size = self.get_smallest_disk_size('hdd')

        # These Variables keep into account only the SSD Disk Type only
        self.disk_ssd = self.has_ssd_disk()
        self.disk_ssd_count = self.get_disk_count('ssd')
        self.disk_ssd_total_size = self.get_total_disk_size('ssd')
        self.disk_ssd_each_size = self.get_smallest_disk_size('ssd')

        # These Variables keep into account only the NVME Disk Type only
        self.disk_nvme = self.has_nvme_disk()
        self.disk_nvme_count = self.get_disk_count('nvme')
        self.disk_nvme_total_size = self.get_total_disk_size('nvme')
        self.disk_nvme_each_size = self.get_smallest_disk_size('nvme')
        
        

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

    def get_url(self):
        # This seems to be the old style URL which appears to not be working anymore
        #return f"https://www.hetzner.com/sb?search={self.id}"

        # This seems to work
        return f"https://www.hetzner.com/sb/#search={self.id}"

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
        excludeProperties = SERVER_PRINT_EXCLUDE_PROPERTIES

        # Initialize Table
        t = Texttable()

        # Get Terminal Width
        terminalSize = os.get_terminal_size()

        # Set Maximum Width for the Table
        t.set_max_width(terminalSize.columns*0.9)

	    # Initialize Variable
        data = []

        # Initialize Variable to Header
        header = ["Property" , "Value"]

        # Loop over Class Properties
        for property in self.__dict__:
            # Name is the same as property
            name = property

            # Check if Property exists in Class
            if property in self.__dict__:
                value = getattr(self, property)
            else:
                value = None

            # Check if this is NOT a Key that must be excluded
            if name not in excludeProperties:
                data.append([name , value , match_criteria , exclude_criteria , match_result , exclude_result , overall_result])

        # Add the Headers to the Table
        t.add_rows([header] , header=True)

        # Add all the Data to the Table
        t.add_rows(data , header=False)

        # Generate String
        str = t.draw()

        # Also add Server URL
        str += "\nServer URL: " + self.get_url() + "\n\n"

        # Return everything indented by a tab
        return '\t'.join(('\n'+str.lstrip()).splitlines(True))



# Define Analyis Class that Extends Server
class Analysis(Server):
    ANALYSIS_FIELDS_NAME = ["matchcriteria" , "excludecriteria" , "matchresult" , "excluderesult" , "overallresult"]
    ANALYSIS_FIELDS_DESCRIPTION = ["Matching Criteria" , "Exclusion Criteria" , "Match Result" , "Exclude Result" , "Overall Result"]

    def __init__(self, server_raw , tax_percent=0):
        # Call Parent Class Constructor
        Server.__init__(self, server_raw , tax_percent)

        # Copy Field Names to the following Fields for easier Debugging
        # self.matchcriteria: tells what the match criteria is (default or set via command line)
        # self.excludecriteria: tells what the exclude criteria is (default or set via command line)
        # self.matchresult: tells if the match criteria is satisfied
        # self.excluderesult: tells if the the excluding criteria is satisfied
        # self.overallresult: tells if the match criteria is satisfied
        self.matchcriteria = dict()
        self.excludecriteria = dict()
        self.matchresult = dict()
        self.excluderesult = dict()
        self.overallresult = dict()

        for property in self.__dict__:
            name = property

            # Exclude the new Fields that we aree introducting
            if (name not in self.ANALYSIS_FIELDS_NAME) and (name not in ["server_raw"]):
                # By default Criteria is Empty String
                self.matchcriteria[name] = ""
                self.excludecriteria[name] = ""

                # By default all Servers Satisfy the Criteria
                self.matchresult[name] = True
                self.excluderesult[name] = True
                self.overallresult[name] = True

    def __repr__(self):
        # Define Properties to Exclude from Print
        excludeProperties = ["server_raw" , *self.ANALYSIS_FIELDS_NAME]

        # Initialize Table
        t = Texttable()

        # Get Terminal Width
        terminalSize = os.get_terminal_size()

        # Set Maximum Width for the Table
        t.set_max_width(terminalSize.columns*0.9)

	    # Initialize Variable
        data = []

        # Initialize Variable to Header
        header = ["Server Property" , "Server Value" , *(self.ANALYSIS_FIELDS_DESCRIPTION)]
        #header.extend(self.ANALYSIS_FIELDS_DESCRIPTION)

        # Limit the Representation to those keys in self.matchcriteria (or self.excludecriteria, self.matchresult, self.excluderesult, self.overallresult)
        for property in self.matchcriteria:
            # Name is the same as property
            name = property

            # Check if Property exists in Class
            if property in self.__dict__:
                value = getattr(self, property)
            else:
                value = None

            # Check if Key exists in Dictionary
            if name in self.matchcriteria:
                match_criteria = self.matchcriteria[name]
            else:
                match_criteria = None

            # Check if Key exists in Dictionary
            if name in self.excludecriteria:
                exclude_criteria = self.excludecriteria[name]
            else:
                exclude_criteria = None

            # Check if Key exists in Dictionary
            if name in self.matchresult:
                match_result = self.matchresult[name]
            else:
                match_result = None

            # Check if Key exists in Dictionary
            if name in self.excluderesult:
                exclude_result = self.excluderesult[name]
            else:
                exclude_result = None

            # Check if Key exists in Dictionary
            if name in self.overallresult:
                overall_result = self.overallresult[name]
            else:
                overall_result = None

            # Check if this is NOT a Key that must be excluded
            if name not in excludeProperties:
                data.append([name , value , match_criteria , exclude_criteria , match_result , exclude_result , overall_result])

        # Add the Headers to the Table
        t.add_rows([header] , header=True)

        # Add all the Data to the Table
        t.add_rows(data , header=False)

        # Generate String
        str = t.draw()

        # Also add Server URL
        str += "\nServer URL: " + self.get_url() + "\n\n"

        # Return everything indented by a tab
        return '\t'.join(('\n'+str.lstrip()).splitlines(True))

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

    # Match a Specific Server ID (Useful for debugging)
    parser.add_argument('--id', dest='id' , nargs=1, required=False, type=str,
                        help='Server IDs (comma separated)')


    # Disk Parameters

    # General (ALL Drive Type/Sizes Together)
    parser.add_argument('--disk-general-count',  dest='disk_general_count' , nargs=1, required=False, type=int,
                        default=[1],
                        help='min disk count')

    parser.add_argument('--disk-general-total-size', dest='disk_general_total_size' , nargs=1, required=False, type=int,
                        help='min disk capacity in total (GB)')

    parser.add_argument('--disk-general-each-size', dest='disk_general_each_size' ,  nargs=1, required=False, type=int,
                        help='min disk capacity per each disk (GB)')


    # Specific Search Option for NVMe/SSD
    parser.add_argument('--disk-quick', dest='disk_quick' , action='store_true',
                        help='require SSD/NVMe')

    parser.add_argument('--disk-quick-count',  dest='disk_quick_count' , nargs=1, required=False, type=int,
                        default=[0],
                        help='min SSD/NVMe disk count')

    parser.add_argument('--disk-quick-total-size', dest='disk_quick_total_size' , nargs=1, required=False, type=int,
                        help='min SSD/NVMe disk capacity in total (GB)')

    parser.add_argument('--disk-quick-each-size', dest='disk_quick_each_size' , nargs=1, required=False, type=int,
                        help='min SSD/NVMe disk capacity per each disk (GB)')

    # Specific Search Option for HDD Only
    parser.add_argument('--disk-hdd', dest='disk_hdd' , action='store_true',
                        help='require HDD')

    parser.add_argument('--disk-hdd-count',  dest='disk_hdd_count' , nargs=1, required=False, type=int,
                        default=[0],
                        help='min HDD disk count')

    parser.add_argument('--disk-hdd-total-size', dest='disk_hdd_total_size' , nargs=1, required=False, type=int,
                        help='min HDD disk capacity in total (GB)')

    parser.add_argument('--disk-hdd-each-size', dest='disk_hdd_each_size' , nargs=1, required=False, type=int,
                        help='min HDD disk capacity per each disk (GB)')

    # Specific Search Option for SSD Only
    parser.add_argument('--disk-ssd', dest='disk_ssd' , action='store_true',
                        help='require SSD')

    parser.add_argument('--disk-ssd-count',  dest='disk_ssd_count' , nargs=1, required=False, type=int,
                        default=[0],
                        help='min SSD disk count')

    parser.add_argument('--disk-ssd-total-size', dest='disk_ssd_total_size' , nargs=1, required=False, type=int,
                        help='min SSD disk capacity in total (GB)')

    parser.add_argument('--disk-ssd-each-size', dest='disk_ssd_each_size' , nargs=1, required=False, type=int,
                        help='min SSD disk capacity per each disk (GB)')
    
    # Specific Search Option for NVMe Only
    parser.add_argument('--disk-nvme', dest='disk_nvme' , action='store_true',
                        help='require NVMe')

    parser.add_argument('--disk-nvme-count',  dest='disk_nvme_count' , nargs=1, required=False, type=int,
                        default=[0],
                        help='min NVMe disk count')

    parser.add_argument('--disk-nvme-total-size', dest='disk_nvme_total_size' , nargs=1, required=False, type=int,
                        help='min NVMe disk capacity in total (GB)')

    parser.add_argument('--disk-nvme-each-size', dest='disk_nvme_each_size' , nargs=1, required=False, type=int,
                        help='min NVMe disk capacity per each disk (GB)')

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
        tax_percent = cli_args.tax_percent[0] if not cli_args.exclude_tax else 0.0
        analysis = Analysis(server_raw, tax_percent)

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
                # This filters out Meta Values / Command Line Options (e.g. --tax or --exclude-tax)
                if name in analysis.matchcriteria:
                    # Add key to match
                    analysis.matchcriteria[name] = value

            # Check for --exclude
            if ("exclude" in key):
                # Adapt key name for self.match[key] addressing
                name = key.replace("exclude_" , "")

                # Only store if the key already exist
                # This filters out Meta Values / Command Line Options (e.g. --tax or --exclude-tax)
                if name in analysis.excludecriteria:
                    # Add key to exclude
                    analysis.excludecriteria[name] = value

        # Tax Percent Match and Exclude make no Sense so just set to None
        analysis.matchcriteria["tax_percent"] = None
        analysis.excludecriteria["tax_percent"] = None

        if cli_args.debug:
            print(json.dumps(server_raw))
        if not cli_args.test_mode and str(analysis.id) in idsProcessed:
            continue


        # Match ID (useful for debugging)
        # Must be converted to Integer
        # If this is not DONE then the evaluation (analysis.id in matchingIDs) below will NOT work
        analysis.matchresult['id'] = True
        if cli_args.id is not None:
            matchingIDs = cli_args.id[0].split(",")
            for i in range(0, len(matchingIDs)):
                matchingIDs[i] = int(matchingIDs[i])
        
            analysis.matchresult['id'] = False if cli_args.id else True
            if analysis.id in matchingIDs:
                analysis.matchresult['id'] = True


        # Match Datacenter
        analysis.matchresult['datacenter'] = False if cli_args.datacenter else True
        if cli_args.datacenter is not None and cli_args.datacenter[0] in analysis.datacenter:
            analysis.matchresult['datacenter'] = True

        # Match Price
        analysis.matchresult['price'] = analysis.price <= cli_args.price[0] if cli_args.price else True

        # Match CPU Count
        analysis.matchresult['cpu_count'] = analysis.cpu_count >= cli_args.cpu_count[
            0] if cli_args.cpu_count else True


        # Match RAM Size
        analysis.matchresult['ram_size'] = analysis.ram_size >= cli_args.ram_size[0] if cli_args.ram_size else True




        # Match General Disk Count
        analysis.matchresult['disk_general_count'] = analysis.disk_general_count >= cli_args.disk_general_count[0] if cli_args.disk_general_count else True

        # Match General Total Disk Size
        analysis.matchresult['disk_general_total_size'] = analysis.disk_general_total_size >= cli_args.disk_general_total_size[
            0] if cli_args.disk_general_total_size else True

        # Match General Each Disk Size
        analysis.matchresult['disk_general_each_size'] = analysis.disk_general_each_size >= cli_args.disk_general_each_size[0] if cli_args.disk_general_each_size else True




        # Match Quick Disk (SSD/NVME)
        analysis.matchresult['disk_quick'] = analysis.has_quick_disk() if cli_args.disk_quick else True

        # Match Quick Disk Count
        analysis.matchresult['disk_quick_count'] = analysis.disk_quick_count >= cli_args.disk_quick_count[0] if cli_args.disk_quick_count else True

        # Match Quick Total Disk Size
        analysis.matchresult['disk_quick_total_size'] = analysis.disk_quick_total_size >= cli_args.disk_quick_total_size[
            0] if cli_args.disk_general_total_size else True

        # Match Quick Each Disk Size
        analysis.matchresult['disk_quick_each_size'] = analysis.disk_quick_each_size >= cli_args.disk_quick_each_size[0] if cli_args.disk_quick_each_size else True



        # Match NVME Disk
        analysis.matchresult['disk_nvme'] = analysis.has_nvme_disk() if cli_args.disk_nvme else True

        # Match NVME Disk Count
        analysis.matchresult['disk_nvme_count'] = analysis.disk_nvme_count >= cli_args.disk_nvme_count[0] if cli_args.disk_nvme_count else True

        # Match NVME Total Disk Size
        analysis.matchresult['disk_nvme_total_size'] = analysis.disk_nvme_total_size >= cli_args.disk_nvme_total_size[
            0] if cli_args.disk_general_total_size else True

        # Match NVME Each Disk Size
        analysis.matchresult['disk_nvme_each_size'] = analysis.disk_nvme_each_size >= cli_args.disk_nvme_each_size[0] if cli_args.disk_nvme_each_size else True




        # Match Special - Hardware Raid
        analysis.matchresult['sp_hw_raid'] = analysis.sp_hw_raid if cli_args.sp_hw_raid else True

        # Match Special - Redundant PSU
        analysis.matchresult['sp_red_psu'] = analysis.sp_red_psu if cli_args.sp_red_psu else True

        # Match Special - ECC RAM
        analysis.matchresult['sp_ecc'] = analysis.sp_ecc if cli_args.sp_ecc else True

        # Match Special - GPU
        analysis.matchresult['sp_gpu'] = analysis.sp_gpu if cli_args.sp_gpu else True

        # Match Special - IPv4
        analysis.matchresult['sp_ipv4'] = analysis.sp_ipv4 if cli_args.sp_ipv4 else True

        # Match Special - Intel NIC
        analysis.matchresult['sp_inic'] = analysis.sp_inic if cli_args.sp_inic else True


        # Match Specific CPUs
        # False by default unless Match is found
        analysis.matchresult['cpu_description'] = False
        if cli_args.match_cpu_description:

            # Split Possible Matches
            # Make sure both the Description and Search Criteria are lowercase in order not to miss any potential Match
            selected_cpu_matches = cli_args.match_cpu_description[0].lower().split(",")

            # Try to see if any Match allowed is found
            for cpu in selected_cpu_matches:
                if cpu in analysis.cpu_description.lower():
                    # Found match
                    analysis.matchresult['cpu_description'] = True
        else:
            # Not Required
            analysis.matchresult['cpu_description'] = True


        # Exclude Specific CPUs
        # True by default unless Match is found
        analysis.excluderesult['cpu_description'] = True
        if cli_args.exclude_cpu_description:
            # Split Possible Matches
            # Make sure both the Description and Search Criteria are lowercase in order not to miss any potential Match
            selected_cpu_exclusions = cli_args.exclude_cpu_description[0].lower().split(",")

            # Try to see if any Match allowed is found
            for cpu in selected_cpu_exclusions:
                if cpu in analysis.cpu_description.lower():
                    # Found exclusion match
                    analysis.excluderesult['cpu_description'] = False
        else:
            # Not Required
            analysis.excluderesult['cpu_description'] = True



        # Update the Overall Criteria (XXX_resulkt = XXX_matches and XXX_excludes)
        analysis.computeOverallResult()

        # Check if Server Satisfies all Criteria of Match+Exclude
        if analysis.fitRequirements():
            # Display Analysis
            print(analysis)

            if not cli_args.test_mode:
                # Send Notification
                send_notification(notifier, analysis, cli_args.send_payload)

                #  Write to File the ID that we processed
                f.write(","+str(analysis.id))

                # If a Database is going to be Introduced later on ...
                # If Server is not Already in the Database with the same Price
                #pass
                #    #send_notification(notifier, analysis, cli_args.send_payload)
                #    #f.write(","+str(analysis.id))

    if not cli_args.test_mode:
        f.close()
