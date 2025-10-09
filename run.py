from app import create_app

app = create_app()

if __name__ == "__main__":
    # Chạy ứng dụng với chế độ debug, dễ dàng cho việc phát triển
    # Port 5000 là port mặc định của Flask
    app.run(host="0.0.0.0", port=5001, debug=True)
