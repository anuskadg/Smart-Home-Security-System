import requests

class TelegramBot:
    def __init__(self, token, chat_id):
        """
        Initialize Telegram Bot with token and chat ID
        
        :param token: Bot token from BotFather
        :param chat_id: Telegram chat ID to send messages to
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text):
        """
        Send text message to Telegram
        
        :param text: Message text to send
        :return: Response from Telegram API
        """
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, params=params)
        return response.json()

    def send_video(self, video_path, caption=None):
        """
        Send video to Telegram
        
        :param video_path: Path to the video file
        :param caption: Optional caption for the video
        :return: Response from Telegram API
        """
        url = f"{self.base_url}/sendVideo"
        with open(video_path, 'rb') as video:
            files = {'video': video}
            params = {
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            response = requests.post(url, params=params, files=files)
        return response.json()

    def send_photo(self, photo_path, caption=None):
        """
        Send photo to Telegram
        
        :param photo_path: Path to the photo file
        :param caption: Optional caption for the photo
        :return: Response from Telegram API
        """
        url = f"{self.base_url}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            params = {
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            response = requests.post(url, params=params, files=files)
        return response.json()