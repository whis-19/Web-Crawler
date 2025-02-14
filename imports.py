import os
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import re
from urllib.parse import urljoin
import threading
import csv
import google.generativeai as genai
import time
