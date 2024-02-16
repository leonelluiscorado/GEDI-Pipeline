import os
import requests
from dotenv import load_dotenv
import getpass
from tqdm import tqdm
import earthaccess

class SessionNASA(requests.Session):
	"""
		DEPRECATED: We use EarthAccess API
	:class: SessionNASA authorizes access to download files from NASA's Data Repository.
	This implementation checks if a .env file exists with said credentials, if not, asks user for input.

	Args:
		username - Registered username for Data Repo
		password - Registered password for Data Repo
	"""
	
	AUTH_HOST = 'urs.earthdata.nasa.gov'

	def __init__(self):
		super().__init__()

		self.__precheck()
		self.auth = (self.username, self.password)

	def __precheck(self):
		if os.path.exists(".env"):
			load_dotenv()
			self.username = os.environ.get("GEDIPIPELINE_USER")
			self.password = os.environ.get("GEDIPIPELINE_PASS")
			return
		
		# If credentials don't exist yet, ask user
		print("[Downloader] Introduce your credentials to access the Data Repository")
		self.username = input("Username : ")
		self.password = getpass.getpass()

 
	def rebuild_auth(self, prepared_request, response):
		"""
		See requests.Session.rebuild_auth docs:
		"When being redirected we may want to strip authentication from the request to avoid leaking credentials.
		This method intelligently removes and reapplies authentication where possible to avoid credential loss."

		Checks if redirected or original URL hostname is the same as AUTH_HOST (NASA Data Repo),
		and deletes authorization credentials when not, to avoid leaking credentials
		"""
		headers = prepared_request.headers 
		url = prepared_request.url
		if 'Authorization' in headers: 
			original_parsed = requests.utils.urlparse(response.request.url) 
			redirect_parsed = requests.utils.urlparse(url) 
			if (original_parsed.hostname != redirect_parsed.hostname) and redirect_parsed.hostname != self.AUTH_HOST and original_parsed.hostname != self.AUTH_HOST: 
				del headers['Authorization']
		return

class GEDIDownloader:
	"""
	The GEDIDownloader :class: implements a downloading mechanism for a given NASA Repository link, while keeping
	an authorization session alive.

	It implements a file chunk downloading mechanism and a file checking step to skip a download or not.

	Args:
		persist_login: Choice to persist login and save to a .netrc file. See Earthdata Access API for more info:
					   https://earthaccess.readthedocs.io/en/latest/howto/authenticate/
		save_path: Absolute path to save the downloaded files. If None, saves to current working directory (script).
	"""

	def __init__(self, persist_login=False, save_path=None):
		self.save_path = save_path if save_path is not None else ""
		self.auth = earthaccess.login(persist=persist_login)
		self.session = self.auth.get_session()
	
	def __download(self, content, save_path, length):

		with open(save_path, "wb") as file, tqdm(total=int(length)) as pbar:
			for chunk in content:
				# Filter out keep alive chunks
				if not chunk:
					continue

				file.write(chunk)
				pbar.update(len(chunk))

	def __precheck_file(self, file_path, size):
		"""
		Prechecking file mechanism function - if not exists or is corrupted (not equal to the download size), it downloads the file.
		"""
		# File does not exist in save_path
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


	def download_granule(self, url, chunk_size=128):
		"""
		This function downloads the file from a given URL. Must keep a Login Session alive.
		Args:
			url: NASA Repo URL to download the file.
			chunk_size: Specify chunk size for download in kilobytes. Defaults to 128 KB.
		"""
		filename = url.split("/")[-1]

		# If even the filename does not have "GEDI" in it, do not download
		if not "GEDI" in filename:
			print(f"[Downloader] Invalid URL {url}. Please check URL and download again.")
			return False

		file_path = os.path.join(self.save_path, filename)
		chunk_size = chunk_size * 1024 # KB chunk

		http_response = self.session.get(url, stream=True)

		# If http response other than OK 200, user needs to check credentials
		if not http_response.ok:
			print(f"[Downloader] Invalid credentials for Login session. You may want to delete the credentials on the '.netrc' file and start over.")
			return False

		response_length = http_response.headers.get('content-length')

		# If file not exists, download
		if not self.__precheck_file(file_path, int(response_length)):
			self.__download(http_response.iter_content(chunk_size=chunk_size), file_path, response_length)

		# Check file integrity / if it downloaded correctly
		if not os.getsize(file_path) == int(response_length):
			# If not downloaded correctly, send message for download retry
			return False

		return True
		