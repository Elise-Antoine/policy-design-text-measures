# Extract bill metadata from a saved NCSL AI Legislation Tracker page.
#
# The National Conference of State Legislatures (NCSL) maintains a
# public tracker of US state-level AI legislation. This script parses a
# locally-saved copy of that tracker page and produces a CSV index of
# bills with their ID, year, status, and topic.
#
# The bill texts themselves are not collected by this script: the NCSL
# tracker links to bill text hosted on external services that do not
# permit automated access. Users wishing to obtain bill texts can either
# follow the links manually, or use LegiScan's API (https://legiscan.com/),
# which provides programmatic access to US state legislation under a
# free non-commercial tier.
#
# Workflow:
#   1. Open https://www.ncsl.org/technology-and-communication/
#      artificial-intelligence-2025-legislation in a browser
#   2. Save the page as HTML to disk (File > Save Page As...)
#   3. Set `input_file` below to point at the saved file
#   4. Run this script
#
# Developed as part of a project measuring stringency and lexical
# diversity in US state AI legislation.

library(rvest)
library(dplyr)
library(stringr)
library(purrr)


# ---- Parameters --------------------------------------------------------------

input_file <- "ncsl_tracker.html"   # Path to the saved NCSL tracker page.
output_csv <- "bill_metadata.csv"   # Output filename for the metadata index.


# ---- Step 1: read the saved tracker page -------------------------------------

if (!file.exists(input_file)) {
  stop("Input HTML file not found at: ", input_file,
       "\nSave the NCSL tracker page locally and set `input_file` to its path.")
}

page <- read_html(input_file)


# ---- Step 2: locate bill entries ---------------------------------------------
# Each bill in the tracker is presented as a link whose text is the bill
# ID (e.g. "CA AB 2013"), surrounded by metadata in the parent HTML
# structure. We locate every link that points at the legislative tracking
# service NCSL uses, then extract metadata from the surrounding context.

bill_links <- page %>% html_nodes("a[href*='statenet.com']")

message("Found ", length(bill_links), " bill entries in the saved page.")


# ---- Step 3: extract metadata for each bill ----------------------------------
# The metadata fields (year, status, topic) live in the text of the
# enclosing container around each link. We pull that container's full
# text and use regular expressions to find the fields we want.
#
# Note: this extraction depends on NCSL's current page structure and may
# need updating if they revise the layout.

extract_metadata <- function(link_node) {

  bill_id <- html_text(link_node, trim = TRUE)

  # Pull the text of the grandparent <div> -- this typically contains
  # the full metadata block surrounding the bill link.
  parent_text <- link_node %>%
    html_node(xpath = "./parent::div/parent::div") %>%
    html_text(trim = TRUE)

  # Year: a four-digit year appearing in the metadata block. Captures
  # any year from 2020 onwards so this script remains useful as the
  # tracker grows.
  year <- str_extract(parent_text, "20\\d{2}")

  # Status: the text between "Status:" and "Date of Last Action".
  status <- str_match(parent_text,
                      "Status:\\s*(.*?)\\s*Date of Last Action")[, 2]

  # Topic: the text between "Topics:" and the next labelled section.
  topic <- str_match(parent_text,
                     "Topics:\\s*(.*?)\\s*(Summary|Associated Bills|$)")[, 2]

  data.frame(
    bill_id = bill_id,
    year    = ifelse(is.na(year),   "Unknown", year),
    status  = ifelse(is.na(status), "Unknown", str_trim(status)),
    topic   = ifelse(is.na(topic),  "Unknown", str_trim(topic)),
    stringsAsFactors = FALSE
  )
}


# ---- Step 4: build the metadata table and write output -----------------------

bill_metadata <- map_df(bill_links, extract_metadata) %>%
  distinct(bill_id, .keep_all = TRUE)

write.csv(bill_metadata, output_csv, row.names = FALSE)

message("Wrote ", nrow(bill_metadata), " bills to ", output_csv, ".")
