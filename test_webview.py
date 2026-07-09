import webview

window = webview.create_window(
    "EDITH Test",
    html="""
    <html>
        <body style="font-family:Arial;text-align:center;margin-top:80px;">
            <h1>EDITH Test</h1>
            <p>If you can see this, pywebview is working correctly.</p>
        </body>
    </html>
    """
)

webview.start()