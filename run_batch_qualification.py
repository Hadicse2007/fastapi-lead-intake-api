
from export_leads import export_leads_to_csv
from qualify_lead import qualify_multiple_leads

# Three sample customer leads
sample_leads = [

    {
        "lead_id": "L001",
        "message": (
            "I run a marketing agency. "
            "I urgently need AI automation "
            "to manage our increasing customer inquiries."
        )
    },

    {
        "lead_id": "L002",
        "message": (
            "We are planning to integrate our CRM "
            "with our existing sales tools next month."
        )
    },

    {
        "lead_id": "L003",
        "message": (
            "Hello, I found your website. "
            "I am just exploring your services. "
            "Can you tell me more?"
        )
    }

]


def main():

    print("Analyzing multiple leads...\n")

    result = qualify_multiple_leads(sample_leads)

    print("BATCH LEAD QUALIFICATION RESULTS")
    print("================================")

    print(result.model_dump_json(indent=2))
    csv_file = export_leads_to_csv(result)

    print(f"\nCSV file created successfully: {csv_file}")


if __name__ == "__main__":
    main()
