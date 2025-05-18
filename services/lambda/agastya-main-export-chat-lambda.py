import boto3
import openpyxl
from openpyxl.styles import Font, Alignment
import io
import json
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from typing import Tuple

CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']
CHAT_MESSAGES_TABLE_NAME = os.environ['CHAT_MESSAGES_TABLE_NAME']
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
CHAT_TRANSCRIPTS_FOLDER_PATH = os.environ['CHAT_TRANSCRIPTS_FOLDER_PATH']

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'MODIFY':
            new_image = record['dynamodb']['NewImage']
            old_image = record['dynamodb']['OldImage']
            
            old_status = old_image.get('session_status', {}).get('S')
            new_status = new_image.get('session_status', {}).get('S')
            
            if old_status == 'active' and new_status == 'ended':
                user_email = new_image['user_email']['S']
                login_session_id = new_image['login_session_id']['S']
                user_full_name = new_image.get('user_full_name', {}).get('S', '')
                
                name_parts = user_full_name.split(' ', 1)
                user_first_name = name_parts[0] if name_parts else ''
                user_last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                export_chat_sessions_to_excel(
                    user_email=user_email,
                    login_session_id=login_session_id,
                    user_first_name=user_first_name,
                    user_last_name=user_last_name
                )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Chat export processing completed')
    }

def formatted_name(student_name: str) -> str:
    return student_name.replace('-', ' ').title()

def export_chat_sessions_to_excel(user_email: str, login_session_id: str, user_first_name: str, user_last_name: str) -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)
        chat_messages_table = dynamodb.Table(CHAT_MESSAGES_TABLE_NAME)
        
        sessions_response = chat_sessions_table.query(
            IndexName='UserSessionsIndex',
            KeyConditionExpression=Key('user_email').eq(user_email),
            FilterExpression=Attr('login_session_id').eq(login_session_id)
        )
        
        if 'Items' not in sessions_response or len(sessions_response['Items']) == 0:
            success = True
            message = f"No chat sessions found for user: {user_email} with login session ID: {login_session_id}"
            print(f"export_chat_sessions_to_excel | {message}")
            return success, message
        
        workbook = openpyxl.Workbook()
        metadata_sheet = workbook.active
        metadata_sheet.title = "Metadata"
        
        metadata_sheet['A1'] = "Login Session ID"
        metadata_sheet['B1'] = "User Email"
        metadata_sheet['C1'] = "User Name"
        metadata_sheet['D1'] = "Student Name"
        metadata_sheet['E1'] = "Chat Session ID"
        metadata_sheet['F1'] = "Started At"
        metadata_sheet['G1'] = "Last Updated At"
        metadata_sheet['H1'] = "Status"
        metadata_sheet['I1'] = "Message Count"
        
        for cell in metadata_sheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='top')
        
        row = 2
        student_sessions = {}
        
        for session in sessions_response['Items']:
            metadata_sheet[f'A{row}'] = session.get('login_session_id', '')
            metadata_sheet[f'B{row}'] = session.get('user_email', '')
            metadata_sheet[f'C{row}'] = session.get('user_full_name', '')
            metadata_sheet[f'D{row}'] = formatted_name(session.get('student_name', ''))
            metadata_sheet[f'E{row}'] = session.get('chat_session_id', '')
            metadata_sheet[f'F{row}'] = session.get('started_at', '')
            metadata_sheet[f'G{row}'] = session.get('last_updated_at', '')
            metadata_sheet[f'H{row}'] = session.get('session_status', '')
            metadata_sheet[f'I{row}'] = session.get('message_count', 0)
            
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                metadata_sheet[f'{col}{row}'].alignment = Alignment(horizontal='left', vertical='top')
            row += 1
            
            student_name = session.get('student_name', '')
            chat_session_id = session.get('chat_session_id', '')
            global_session_id = session.get('global_session_id', '')
            
            if student_name and chat_session_id and global_session_id:
                student_sessions[student_name] = {
                    'chat_session_id': chat_session_id,
                    'global_session_id': global_session_id
                }
        
        for column in metadata_sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            metadata_sheet.column_dimensions[column_letter].width = adjusted_width
        
        for student_name, session_info in student_sessions.items():
            global_session_id = session_info['global_session_id']
            
            messages_response = chat_messages_table.query(
                KeyConditionExpression=Key('global_session_id').eq(global_session_id),
                ScanIndexForward=True
            )
            
            if 'Items' not in messages_response or len(messages_response['Items']) == 0:
                continue
            
            sheet_name = formatted_name(student_name)
            sheet_name = sheet_name[:31].replace(':', '').replace('\\', '').replace('/', '').replace('?', '').replace('*', '').replace('[', '').replace(']', '')
            chat_sheet = workbook.create_sheet(title=sheet_name)
            
            chat_sheet['A1'] = "Timestamp"
            chat_sheet['B1'] = "Role"
            chat_sheet['C1'] = "Message"
            chat_sheet['D1'] = "Message_Kannada"
            chat_sheet['E1'] = "Input Type"
            
            for cell in chat_sheet[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='top')
            
            row = 2
            for message in messages_response['Items']:
                if message.get('input_type') == 'system':
                    continue
                chat_sheet[f'A{row}'] = message.get('created_at', '')
                chat_sheet[f'B{row}'] = message.get('role', '')
                chat_sheet[f'C{row}'] = message.get('message', '')
                chat_sheet[f'D{row}'] = message.get('message_kannada', '')
                chat_sheet[f'E{row}'] = message.get('input_type', '')
                
                for col in ['A', 'B', 'C', 'D', 'E']:
                    chat_sheet[f'{col}{row}'].alignment = Alignment(horizontal='left', vertical='top')
                row += 1
            
            for column in chat_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 100)
                chat_sheet.column_dimensions[column_letter].width = adjusted_width
            
            for row_idx in range(2, row):
                for col in ['C', 'D']:
                    cell = chat_sheet[f'{col}{row_idx}']
                    cell.alignment = Alignment(horizontal='left', vertical='top', wrapText=True)
        
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        
        s3_client = boto3.client('s3')
        date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m")
        if month == '01':
            month = 'January'
        elif month == '02':
            month = 'February'
        elif month == '03':
            month = 'March'
        elif month == '04':
            month = 'April'
        elif month == '05':
            month = 'May'
        elif month == '06':
            month = 'June'
        elif month == '07':
            month = 'July'
        elif month == '08':
            month = 'August'
        elif month == '09':
            month = 'September'
        elif month == '10':
            month = 'October'
        elif month == '11':
            month = 'November'
        elif month == '12':
            month = 'December'
        date = datetime.now().strftime("%d")
        s3_key = f"{CHAT_TRANSCRIPTS_FOLDER_PATH}/{user_email}/{year}/{month}/{date}/{login_session_id}.xlsx"
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=buffer,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        success = True
        message = f"Successfully exported chat transcripts to {s3_key}"
        print(f"export_chat_sessions_to_excel | {message}")
    except Exception as e:
        message = f"Error exporting chat sessions to Excel: {str(e)}"
        print(f"export_chat_sessions_to_excel | {message}")
    
    return success, message