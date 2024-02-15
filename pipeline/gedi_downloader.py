import os
import requests
from tqdm import tqdm

class SessionNASA(requests.Session):
	
	AUTH_HOST = 'urs.earthdata.nasa.gov'

	def __init__(self, username, password):
		super().__init__() 
		self.auth = (username, password)
 
	def rebuild_auth(self, prepared_request, response): 
		headers = prepared_request.headers 
		url = prepared_request.url
		if 'Authorization' in headers: 
			original_parsed = requests.utils.urlparse(response.request.url) 
			redirect_parsed = requests.utils.urlparse(url) 
			if (original_parsed.hostname != redirect_parsed.hostname) and redirect_parsed.hostname != self.AUTH_HOST and original_parsed.hostname != self.AUTH_HOST: 
				del headers['Authorization']
		return

class GEDIDownloader:

	def __init__(self, username, password, save_path=None):
		self.save_path = save_path
		self.session = SessionNASA(username, password)
	
	def _download(self, content, save_path, length):
		with open(save_path, "wb") as file, tqdm(total=int(length)) as pbar:

			for chunk in content:
				# Filter out keep alive chunks
				if not chunk:
					continue

				file.write(chunk)
				pbar.update(len(chunk))

	def _check_file_integrity(self, file_path, size):
		return os.path.getsize(file_path) == size


	def _precheck_file(self, file_path, size):
		if not os.path.exists(file_path):
			print(f"[Downloader] Downloading granule and saving \"{file_path}\"...")
			return False

		# File exists but not complete, restart download
		if os.path.getsize(file_path) != size:
			print(f"[Downloader] File at \"{file_path}\" exists but corrupted. Downloading again...")
			# Delete file and restart download
			os.remove(file_path)
			return False

		# File exists and complete, skip download
		print(f"[Downloader] File at \"{file_path}\" exists. Skipping download...")
		return True

	def download_granule(self, url):
		filename = url.split("/")[-1]
		file_path = os.path.join(self.save_path, filename)
		chunk_size = 1024 * 128 # 128KB chunk

		http_response = self.session.get(url, stream=True)
		response_length = http_response.headers.get('content-length')

		# If file not exists, download
		if not self._precheck_file(file_path, int(response_length)):
			self._download(http_response.iter_content(chunk_size=chunk_size), file_path, response_length)

		if not self._check_file_integrity(file_path, int(response_length)):
			# File not downloaded correctly, send message for download retry
			return False

		return True
		