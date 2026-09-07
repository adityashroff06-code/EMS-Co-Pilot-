"""Optional local dashboard. Start with: python app.py --db ems.db"""

import argparse

from ems_copilot import EnergyDataset, render_markdown


def build_app(dataset):
    import gradio as gr

    def report(start, end):
        try:
            return render_markdown(dataset.snapshot(start, end))
        except ValueError as error:
            return f"Unable to build report: {error}"

    return gr.Interface(
        fn=report,
        inputs=[gr.Textbox(value="2018-01-01", label="Start date (YYYY-MM-DD)"),
                gr.Textbox(value="2018-01-07", label="End date (YYYY-MM-DD)")],
        outputs=gr.Markdown(),
        title="EMS Co-Pilot",
        description="Explore the steel-plant energy dataset. Reports include coverage and duplicate handling. Carbon totals reflect the supplied dataset.",
        examples=[["2018-01-01", "2018-01-07"], ["2018-02-01", "2018-02-28"]],
        flagging_mode="never",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="ems.db")
    args = parser.parse_args()
    build_app(EnergyDataset(args.db)).launch(server_name="127.0.0.1", share=False)
