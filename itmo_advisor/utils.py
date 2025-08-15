# utils.py
import argparse, os
from dotenv import load_dotenv
from repository import Repository

def build_repo() -> Repository:
    return Repository()

def load_env():
    load_dotenv()