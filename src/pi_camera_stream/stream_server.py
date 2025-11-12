from .web_server import app


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    print("[INFO] Starting Flask server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)


if __name__ == "__main__":
    main()