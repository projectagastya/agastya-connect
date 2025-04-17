from configure_logger import backend_logger
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class StudentProfileSchema(BaseModel):
    student_name: str = Field(..., description="Name of the student.")
    student_sex: Literal["male", "female"] = Field(..., description="Sex of the student.")
    student_age: Optional[int] = Field(None, description="Age of the student.")
    student_state: str = Field(..., description="State of the student.")
    student_image: Optional[str] = Field(None, description="Image of the student.")

class GetStudentProfilesRequest(BaseModel):
    count: int = Field(..., description="Number of student profiles to retrieve.")

    @field_validator("count")
    def validate_count(cls, v):
        if v <= 0:
            raise ValueError("Count must be greater than 0")
        return v

class GetStudentProfilesResponse(BaseModel):
    success: bool = Field(..., description="Whether the function call was successful.")
    message: str | None = Field(None, description="Message if the student profiles were retrieved successfully.")
    result: bool = Field(..., description="Whether the student profiles were retrieved successfully.")
    data: list[StudentProfileSchema] | None = Field(None, description="Student profiles data if the retrieval was successful.")
    timestamp: str | None = Field(None, description="Timestamp of the student profiles retrieval.")

class StartEndChatRequest(BaseModel):
    user_first_name: str = Field(..., min_length=1, description="First name of the user.")
    user_last_name: str = Field(..., min_length=1, description="Last name of the user.")
    user_email: str = Field(..., min_length=1, description="Email of the user to initialize the chat session for.")
    login_session_id: str = Field(..., min_length=1, description="Login session ID for which the chat session needs to be initialized.")
    chat_session_id: str = Field(..., min_length=1, description="Chat session ID for which the vectorstore needs to be initialized.")
    student_name: str = Field(..., min_length=1, description="Name of the student to initialize the chat session for.")

    @field_validator("user_first_name")
    def validate_user_first_name(cls, v):
        if not v.strip():
            raise ValueError("First name cannot be a blank string")
        return v
    
    @field_validator("user_last_name")
    def validate_user_last_name(cls, v):
        if not v.strip():
            raise ValueError("Last name cannot be a blank string")
        return v
    
    @field_validator("user_email")
    def validate_email(cls, v):
        if not v.strip():
            raise ValueError("Email cannot be a blank string")
        return v
    
    @field_validator("student_name")
    def validate_student_name(cls, v):
        if not v.strip():
            raise ValueError("Student name cannot be a blank string")
        return v
    
    @field_validator("login_session_id")
    def validate_login_session_id(cls, v):
        if not v.strip():
            raise ValueError("Login session ID cannot be a blank string")
        return v
    
    @field_validator("chat_session_id")
    def validate_chat_session_id(cls, v):
        if not v.strip():
            raise ValueError("Chat session ID cannot be a blank string")
        return v

class StartChatResponse(BaseModel):
    success: bool = Field(..., description="Whether the chat session was initialized successfully.")
    message: str | None = Field(None, description="Message if the chat session was initialized successfully.")
    result: bool | None = Field(None, description="Whether the chat session was initialized successfully.")
    data: str | None = Field(None, description="The first message to be sent to the user.")
    timestamp: str | None = Field(None, description="Timestamp of the chat session initialization.")

class ChatMessageRequest(BaseModel):
    login_session_id: str = Field(..., min_length=1, description="Login session ID for which the chat session needs to be initialized.")
    chat_session_id: str = Field(..., min_length=1, description="Unique identifier for the chat session.")
    question: str = Field(..., min_length=1, description="The question being asked to the LLM.")
    input_type: Literal["audio", "button", "default", "manual", "system"] = Field(..., description="The type of input being provided to the LLM.")
    student_name: str = Field(..., min_length=1, description="The student involved in this conversation")
    user_full_name: str = Field(..., min_length=1, description="The user asking the question")
    user_email: Optional[str] = Field(None, description="Email of the user (added for DynamoDB)")

    @field_validator("login_session_id")
    def validate_login_session_id(cls, v):
        if not v.strip():
            raise ValueError("Login session ID cannot be a blank string")
        return v
    
    @field_validator("chat_session_id")
    def validate_chat_session_id(cls, v):
        if not v.strip():
            raise ValueError("Chat session ID cannot be a blank string")
        return v
    
    @field_validator("question")
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Your question cannot be blank")
        return v
    
    @field_validator("input_type")
    def validate_input_type(cls, v):
        if v not in ["audio", "button", "default", "manual", "system"]:
            raise ValueError("Invalid input type")
        return v

class ChatMessageResponse(BaseModel):
    success: bool = Field(..., description="Whether the function call was successful.")
    message: str | None = Field(None, description="Message if the chat message was retrieved successfully.")
    result: bool | None = Field(None, description="Whether the chat message was retrieved successfully.")
    data: str | None = Field(None, description="The response generated by the model.")
    timestamp: str | None = Field(None, description="Timestamp of the chat message retrieval.")
    
class EndChatResponse(BaseModel):
    success: bool = Field(..., description="Whether the function call was successful.")
    message: str | None = Field(None, description="Message if the chat session was ended successfully.")
    timestamp: str | None = Field(None, description="Timestamp of the chat session end.")