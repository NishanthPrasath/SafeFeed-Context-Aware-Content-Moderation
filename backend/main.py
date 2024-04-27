import os
import sqlite3
from fastapi import FastAPI, Response
from dotenv import load_dotenv
import boto3
import base_model
import basic_func
import pandas as pd
import streamlit as st
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import json
from datetime import datetime, timedelta
import io
from fastapi.responses import StreamingResponse


app =FastAPI()

load_dotenv()



@app.post("/scrape-reddit-policies", tags=["Reddit Policies"])
async def scrape_reddit_policies_f() -> dict:

    basic_func.scrape_reddit_policies()

    return {"output" : "Successfully Scraped!"}



@app.post("/upload-policies-to-snowflake", tags=["Reddit Policies"])
async def upload_policies_to_snowflake_f() -> dict:

    basic_func.upload_policies_to_snowflake()

    return {"output" : "Successfully Uploaded!"}



@app.post("/vectorize-policies", tags=["Reddit Policies"])
async def vectorize_policies_f() -> dict:

    basic_func.vectorize_policies()

    return {"output" : "Successfully Uploaded!"}



@app.post("/llm-response", tags=["Reddit Policies"])
async def llm_response_f(text: str) -> dict:

    policies = basic_func.similarity_search(text)

    generated_response = basic_func.check_policies(text, policies)

    return {"generated_response" : generated_response}