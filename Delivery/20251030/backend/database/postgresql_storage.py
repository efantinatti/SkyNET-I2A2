"""
PostgreSQL storage implementation using psycopg2 for direct database access.
This replaces the HTTP-based SupabaseStorage for better performance.
"""
import json
import logging
import re
import traceback
import decimal
from enum import Enum
from typing import Dict, Any, List, Optional, Union, TypeVar, Type, AnyStr

# Import psycopg2 only when needed to avoid import errors
try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extras import Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    Json = None

from datetime import datetime, timezone, UTC, date, time


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and other non-serializable types."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, (decimal.Decimal, float)):
            return float(obj)
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def safe_json_serialize(data: Any) -> str:
    """Safely serialize data to JSON, handling non-serializable types."""
    try:
        return json.dumps(data, cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error serializing to JSON: {e}, data: {str(data)[:200]}")
        # Fallback: convert to string representation
        try:
            return json.dumps(str(data), ensure_ascii=False)
        except:
            return '{}'  # Return empty object as last resort

from config import DATABASE_CONFIG
from .base_storage import (
    StorageInterface,
    PaginatedResponse,
    StorageError,
    generate_id,
    get_current_timestamp
)

logger = logging.getLogger(__name__)


class PostgreSQLStorageError(StorageError):
    """PostgreSQL-specific storage errors."""
    pass


class PostgreSQLStorage(StorageInterface):
    """PostgreSQL storage implementation using psycopg2."""

    def __init__(self):
        if not PSYCOPG2_AVAILABLE:
            raise PostgreSQLStorageError(
                "psycopg2 is not available. Install with: pip install psycopg2-binary"
            )

        self.db_config = DATABASE_CONFIG
        self._connection = None

    def _get_connection(self):
        """Get database connection, creating if necessary."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(**self.db_config)
                # Enable autocommit to avoid manual transaction management
                self._connection.autocommit = True
                logger.info("Database connection established with autocommit enabled")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise PostgreSQLStorageError(f"Database connection failed: {e}")
        return self._connection

    def _execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """Execute a query and return results based on fetch type."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or ())

                if fetch == "all":
                    return cursor.fetchall()
                elif fetch == "one":
                    return cursor.fetchone()
                elif fetch == "count":
                    return cursor.fetchone()['count']
                else:
                    return cursor.rowcount

        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise PostgreSQLStorageError(f"Query execution failed: {e}")

    def _get_table_columns(self) -> List[str]:
        """Get list of existing columns in fiscal_documents table."""
        try:
            query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'fiscal_documents'
            ORDER BY ordinal_position
            """
            result = self._execute_query(query, fetch="all")
            return [row['column_name'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting table columns: {e}")
            # Return a basic set of known columns if query fails
            return ['id', 'file_name', 'document_type', 'document_number', 'issuer_cnpj',
                   'issuer_name', 'extracted_data', 'validation_status', 'classification',
                   'created_at', 'updated_at', 'cfop', 'issue_date', 'total_value',
                   'validation_details', 'raw_text', 'uploaded_at', 'processed_at']

    def save_fiscal_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Save a fiscal document to PostgreSQL."""
        # Generate ID if not provided
        if "id" not in document or not document["id"]:
            document["id"] = generate_id()
            document["created_at"] = get_current_timestamp()

        document["updated_at"] = get_current_timestamp()

        # Prepare the query
        columns = list(document.keys())
        values = list(document.values())
        placeholders = ", ".join(["%s"] * len(columns))

        # Convert datetime objects to strings for JSON serialization
        for i, value in enumerate(values):
            if isinstance(value, datetime):
                values[i] = value.isoformat()
            elif columns[i] == 'issue_date' and value is not None:
                # Convert date strings to proper format if needed
                try:
                    if isinstance(value, str) and '/' in value:
                        # Try to parse Brazilian format DD/MM/YYYY
                        if len(value.split('/')) == 3:
                            parts = value.split('/')
                            if len(parts[0]) == 2 and len(parts[1]) == 2:  # DD/MM/YYYY
                                dt = datetime.strptime(value, '%d/%m/%Y')
                                values[i] = dt.strftime('%Y-%m-%dT00:00:00Z')
                            elif len(parts[2]) == 2:  # DD/MM/YY
                                dt = datetime.strptime(value, '%d/%m/%y')
                                values[i] = dt.strftime('%Y-%m-%dT00:00:00Z')
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse date format: {value}")

        # Debug: Log all fields and their types
        logger.debug("=== DEBUG save_fiscal_document ===")
        for col, value in zip(columns, values):
            logger.debug(f"Field: {col} = {type(value)} - {str(value)[:100]}...")
        logger.debug("=== END DEBUG ===")

        # Convert dict/list objects to JSON strings for JSONB columns
        jsonb_fields = ['extracted_data', 'classification', 'validation_details', 'metadata', 'document_data', 'analyses']
        for i, (col, value) in enumerate(zip(columns, values)):
            if col in jsonb_fields and value is not None:
                if not isinstance(value, (str, bytes, bytearray)):
                    logger.debug(f"Converting {col} to JSON: {type(value)}")
                    try:
                        values[i] = json.dumps(value, ensure_ascii=False)
                        logger.debug(f"Successfully converted {col} to JSON")
                    except Exception as json_error:
                        logger.error(f"Error converting {col} to JSON: {json_error}")
                        logger.error(f"Field value: {value}")
                        logger.error(f"Field value type: {type(value)}")
                        raise

        # Convert numeric fields from Brazilian format to American format
        numeric_fields = ['total_value', 'base_calculo_icms', 'valor_icms', 'base_calculo_icms_st', 'valor_icms_st']
        for i, (col, value) in enumerate(zip(columns, values)):
            if col in numeric_fields and value is not None:
                try:
                    # Convert Brazilian number format to float
                    if isinstance(value, str):
                        # Remove currency symbols and spaces
                        clean_value = re.sub(r'[R$\s]', '', value)
                        # Convert Brazilian format (1.234,56) to American format (1234.56)
                        if ',' in clean_value and '.' in clean_value:
                            clean_value = clean_value.replace('.', '').replace(',', '.')
                        elif ',' in clean_value:
                            clean_value = clean_value.replace(',', '.')
                        values[i] = float(clean_value)
                        logger.debug(f"Converted {col} from '{value}' to {values[i]}")
                    else:
                        values[i] = float(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert {col} value '{value}' to number: {e}")
                    values[i] = 0.0

        # Check if columns exist in the table before executing query
        try:
            # Get existing columns from the table
            existing_columns = self._get_table_columns()
            logger.debug(f"Existing columns in fiscal_documents: {existing_columns}")

            # Filter out columns that don't exist in the table
            filtered_columns = []
            filtered_values = []
            for col, value in zip(columns, values):
                if col in existing_columns:
                    filtered_columns.append(col)
                    filtered_values.append(value)
                else:
                    logger.warning(f"Column '{col}' does not exist in fiscal_documents table, skipping")

            if not filtered_columns:
                raise PostgreSQLStorageError("No valid columns to save")

            columns = filtered_columns
            values = filtered_values
            placeholders = ", ".join(["%s"] * len(columns))

        except Exception as e:
            logger.error(f"Error checking table columns: {e}")
            # Continue with original columns if check fails

        query = f"""
        INSERT INTO fiscal_documents ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (id)
        DO UPDATE SET
            {", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "id"])}
        RETURNING *
        """

        try:
            # Debug: Log query and parameters
            logger.debug(f"Executing query: {query}")
            logger.debug(f"Parameters: {len(tuple(values))} params")
            for i, (col, val) in enumerate(zip(columns, values)):
                logger.debug(f"  Param {i}: {col} = {type(val)} - {str(val)[:100]}...")

            result = self._execute_query(query, tuple(values), "one")
            if result:
                # Convert result back to dict format expected by the interface
                saved_doc = dict(result)

                # Convert JSONB fields back from string to dict/list (same as get_fiscal_document)
                jsonb_fields = ['extracted_data', 'classification', 'validation_details', 'metadata', 'document_data', 'analyses']
                for field in jsonb_fields:
                    if field in saved_doc and saved_doc[field] is not None:
                        if isinstance(saved_doc[field], str):
                            try:
                                saved_doc[field] = json.loads(saved_doc[field])
                            except (json.JSONDecodeError, TypeError):
                                # Keep as string if cannot decode
                                pass

                logger.info(f"Document saved successfully. ID: {saved_doc['id']}")
                return saved_doc
            else:
                raise PostgreSQLStorageError("Failed to save document - no result returned")

        except Exception as e:
            logger.error(f"Error saving document: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Columns: {columns}")
            logger.error(f"Values types: {[type(v).__name__ for v in values]}")
            raise PostgreSQLStorageError(f"Failed to save document: {e}")

    def get_fiscal_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single fiscal document by ID."""
        query = "SELECT * FROM fiscal_documents WHERE id = %s"
        logger.debug(f"Searching for document with ID: {doc_id}")
        result = self._execute_query(query, (doc_id,), "one")
        if result:
            logger.debug(f"Document found: {result['id']}")
            # Convert result back to dict format expected by the interface
            doc = dict(result)

            # Convert JSONB fields back from string to dict/list
            jsonb_fields = ['extracted_data', 'classification', 'validation_details', 'metadata', 'document_data', 'analyses']
            for field in jsonb_fields:
                if field in doc and doc[field] is not None:
                    if isinstance(doc[field], str):
                        try:
                            doc[field] = json.loads(doc[field])
                        except (json.JSONDecodeError, TypeError):
                            # Keep as string if cannot decode
                            pass

            return doc
        else:
            logger.debug(f"Document not found with ID: {doc_id}")
        return None

    def get_fiscal_documents(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str = 'created_at',
        order_direction: str = 'desc',
        **filters
    ) -> PaginatedResponse:
        """Get a paginated list of fiscal documents with optional filtering."""

        # Handle page_size=0 as "use default"
        if page_size <= 0:
            page_size = 10  # Default page size

        # Build WHERE clause
        where_conditions = []
        params = []
        param_index = 1

        for key, value in filters.items():
            if value is not None and value != "":
                # Tratamento especial para filtro de data
                if key == 'created_after':
                    where_conditions.append("created_at >= %s")
                    params.append(value)
                elif key == 'created_before':
                    where_conditions.append("created_at < %s")
                    params.append(value)
                # Campos UUID devem usar igualdade exata, não ILIKE
                elif key in ['id', 'fiscal_document_id', 'session_id']:  # Campos UUID em várias tabelas
                    where_conditions.append(f"{key} = %s")
                    params.append(value)
                elif key in ['issuer_cnpj', 'recipient_cnpj']:
                    # Remove formatting for CNPJ search
                    value = ''.join(filter(str.isdigit, str(value)))
                    where_conditions.append(f"REPLACE({key}, '.', '') ILIKE %s")
                    params.append(f"%{value}%")
                else:
                    where_conditions.append(f"{key} ILIKE %s")
                    params.append(f"%{value}%")
                param_index += 1

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get total count
        count_query = f"SELECT COUNT(*) FROM fiscal_documents{where_clause}"
        total_result = self._execute_query(count_query, tuple(params), "count")
        if isinstance(total_result, list):
            if total_result and isinstance(total_result[0], dict) and 'count' in total_result[0]:
                total = total_result[0]['count']
            elif total_result:
                total = total_result[0]
            else:
                total = 0
        else:
            total = total_result

        # Get paginated results
        offset = (page - 1) * page_size
        
        # Validate order_by to prevent SQL injection
        allowed_order_by = ['created_at', 'updated_at', 'issue_date', 'total_value', 'document_type']
        if order_by not in allowed_order_by:
            order_by = 'created_at'
            
        order_direction = 'DESC' if order_direction.lower() == 'desc' else 'ASC'
        
        query = f"""
        SELECT * FROM fiscal_documents{where_clause}
        ORDER BY {order_by} {order_direction}
        LIMIT %s OFFSET %s
        """

        items = self._execute_query(query, tuple(params) + (page_size, offset), "all")
        items = [dict(item) for item in items] if items else []

        # Convert JSONB fields back from string to dict/list for each item
        jsonb_fields = ['extracted_data', 'classification', 'validation_details', 'metadata', 'document_data', 'analyses']
        for item in items:
            for field in jsonb_fields:
                if field in item and item[field] is not None:
                    if isinstance(item[field], str):
                        try:
                            item[field] = json.loads(item[field])
                        except (json.JSONDecodeError, TypeError):
                            # Keep as string if cannot decode
                            pass

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def delete_fiscal_document(self, doc_id: str) -> bool:
        """Delete a fiscal document by ID."""
        query = "DELETE FROM fiscal_documents WHERE id = %s"
        result = self._execute_query(query, (doc_id,))
        return result > 0

    def add_document_analysis(self, doc_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add an analysis to a document."""
        # First, get the document
        document = self.get_fiscal_document(doc_id)
        if not document:
            raise PostgreSQLStorageError(f"Document {doc_id} not found")

        # Add analysis to document
        if "analyses" not in document:
            document["analyses"] = []

        # Generate analysis ID
        analysis_id = len(document["analyses"]) + 1
        analysis["id"] = analysis_id
        analysis["created_at"] = get_current_timestamp()

        document["analyses"].append(analysis)
        document["updated_at"] = get_current_timestamp()

        # Update the document
        return self.save_fiscal_document(document)

    def save_history(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Save a history event.
        
        Args:
            event: Dicionário contendo os dados do evento, incluindo:
                - fiscal_document_id: ID do documento fiscal relacionado
                - event_type: Tipo do evento (ex: 'created', 'updated', 'validated')
                - event_data: Dados adicionais do evento (será convertido para JSON)
                - id: Opcional, será gerado se não fornecido
                - created_at: Opcional, será definido como agora se não fornecido
                
        Returns:
            Dicionário com os dados do evento salvo, incluindo o ID gerado
            
        Raises:
            ValueError: Se fiscal_document_id não for fornecido
            PostgreSQLStorageError: Se ocorrer um erro ao salvar no banco de dados
        """
        # Fazer uma cópia para não modificar o dicionário original
        event = event.copy()
        
        if "fiscal_document_id" not in event:
            # Para compatibilidade com versões antigas
            if "document_id" in event:
                event["fiscal_document_id"] = event.pop("document_id")
            else:
                raise ValueError("fiscal_document_id é obrigatório nos dados do evento")

        # Gerar ID e timestamp se não fornecidos
        if "id" not in event:
            event["id"] = generate_id()
        if "created_at" not in event:
            event["created_at"] = get_current_timestamp()

        # Converter event_data para JSON se for um dicionário
        if "event_data" in event and event["event_data"] is not None:
            if not isinstance(event["event_data"], (str, bytes, bytearray)):
                event["event_data"] = json.dumps(event["event_data"], ensure_ascii=False)

        # Preparar a query
        columns = list(event.keys())
        values = list(event.values())
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
        INSERT INTO document_history ({", ".join(columns)})
        VALUES ({placeholders})
        RETURNING *
        """

        try:
            result = self._execute_query(query, tuple(values), "one")
            if result:
                saved_event = dict(result)
                # Converter event_data de volta para dicionário se for uma string JSON
                if 'event_data' in saved_event and isinstance(saved_event['event_data'], str):
                    try:
                        saved_event['event_data'] = json.loads(saved_event['event_data'])
                    except (json.JSONDecodeError, TypeError):
                        # Maném como string se não for possível decodificar
                        pass
                logger.debug(f"Evento de histórico salvo com sucesso. ID: {saved_event['id']}")
                return saved_event
            else:
                raise PostgreSQLStorageError("Falha ao salvar o evento de histórico - nenhum resultado retornado")

        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {values}")
            raise PostgreSQLStorageError(f"Falha ao salvar histórico: {e}")

    def get_document_history(self, fiscal_document_id: str) -> List[Dict[str, Any]]:
        """Obtém o histórico de eventos para um documento.
        
        Args:
            fiscal_document_id: ID do documento fiscal
            
        Returns:
            Lista de dicionários contendo os eventos de histórico do documento,
            com event_data convertido de volta para dicionário quando apropriado
        """
        query = """
        SELECT * FROM document_history
        WHERE fiscal_document_id = %s
        ORDER BY created_at DESC
        """
        try:
            results = self._execute_query(query, (fiscal_document_id,), "all")
            
            if not results:
                return []
                
            # Converter os resultados para dicionários e processar event_data
            history_events = []
            for result in results:
                event = dict(result)
                
                # Converter event_data de volta para dicionário se for uma string JSON
                if 'event_data' in event and event['event_data'] is not None:
                    if isinstance(event['event_data'], str):
                        try:
                            event['event_data'] = json.loads(event['event_data'])
                        except (json.JSONDecodeError, TypeError):
                            # Manter como está se não for possível decodificar
                            pass
                    # Se for um objeto JSONB do PostgreSQL, já deve vir como dicionário
                    
                history_events.append(event)
                
            return history_events
            
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico do documento {fiscal_document_id}: {e}")
            # Retornar lista vazia em caso de erro para não quebrar o fluxo da aplicação
            return []

    def create_chat_session(self, session_name: str = None) -> Dict[str, Any]:
        """Create a new chat session."""
        try:
            query = """
                INSERT INTO chat_sessions (title)
                VALUES (%s)
                RETURNING *
            """
            result = self._execute_query(query, (session_name or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",), "one")

            if result:
                return dict(result)
            else:
                raise PostgreSQLStorageError("Failed to create chat session")

        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise

    def save_chat_message(self, session_id: str, message_type: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Save a message to the chat session.
        
        Args:
            session_id: ID da sessão de chat
            message_type: Tipo da mensagem (user, assistant, system)
            content: Conteúdo da mensagem
            metadata: Metadados adicionais (serão serializados para JSON)
        """
        try:
            # Garante que o metadata seja um dicionário
            if metadata is None:
                metadata = {}
                
            # Remove objetos datetime ou outros não serializáveis
            safe_metadata = {}
            for k, v in metadata.items():
                try:
                    # Tenta serializar o valor para ver se é válido
                    json.dumps({k: v}, cls=CustomJSONEncoder)
                    safe_metadata[k] = v
                except (TypeError, OverflowError) as e:
                    logger.warning(f"Removendo campo não serializável dos metadados: {k}={v}")
                    continue
                    
            query = """
                INSERT INTO chat_messages (session_id, message_type, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
            """
            
            result = self._execute_query(
                query, 
                (session_id, message_type, content, Json(safe_metadata, dumps=safe_json_serialize)), 
                fetch="one"
            )
            
            logger.info(f"✅ Mensagem salva - ID: {result['id']}, Tipo: {message_type}, Sessão: {session_id}")
            logger.debug(f"Conteúdo: {content[:100]}...")

        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            logger.error(f"Session ID: {session_id}, Type: {message_type}")
            logger.error(f"Content: {content}")
            logger.error(f"Metadata type: {type(metadata).__name__}")
            
            # Tenta registrar os metadados de forma segura
            try:
                logger.error(f"Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
                # Tenta serializar os metadados para diagnóstico
                safe_meta = {}
                if metadata:
                    for k, v in metadata.items():
                        try:
                            safe_meta[k] = type(v).__name__
                        except:
                            safe_meta[k] = 'unserializable'
                logger.error(f"Metadata types: {safe_meta}")
            except Exception as meta_error:
                logger.error(f"Could not log metadata details: {meta_error}")
                
            # Tenta salvar uma versão simplificada da mensagem
            try:
                self._execute_query(
                    """
                    INSERT INTO chat_messages (session_id, message_type, content, metadata)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, message_type, content, Json({'error': 'original_metadata_not_serializable'})),
                    fetch=None
                )
                logger.info("✅ Mensagem salva com metadados reduzidos devido a erro de serialização")
            except Exception as fallback_error:
                logger.error(f"Falha ao salvar mensagem simplificada: {fallback_error}")
                
            raise

    def get_chat_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat messages for a session."""
        try:
            logger.info(f"🔍 Buscando mensagens para a sessão: {session_id}")
            
            # Primeiro, verifica se a sessão existe
            session_check = self._execute_query(
                "SELECT id FROM chat_sessions WHERE id = %s",
                (session_id,),
                fetch="one"
            )
            
            if not session_check:
                logger.error(f"Sessão não encontrada: {session_id}")
                return []
            
            # Busca as mensagens
            query = """
                SELECT id, session_id, message_type, content, created_at, metadata
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at ASC
                LIMIT %s
            """
            results = self._execute_query(query, (session_id, limit), fetch="all")
            logger.info(f"📨 Mensagens encontradas: {len(results)} para a sessão {session_id}")

            # Converte os resultados
            messages = []
            for idx, result in enumerate(results, 1):
                try:
                    msg = dict(result)
                    if msg.get('metadata') and not isinstance(msg['metadata'], dict):
                        msg['metadata'] = {}
                    messages.append(msg)
                    logger.debug(f"Mensagem {idx}: {msg.get('message_type')} - {msg.get('content')[:50]}...")
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem {idx}: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []

    def get_chat_context(self, session_id: str, limit: int = 5) -> str:
        """Get recent chat messages as context for the LLM."""
        try:
            messages = self.get_chat_messages(session_id, limit * 2)  # Get more messages and reverse

            if not messages:
                return "Esta é uma nova conversa."

            # Reverse to show chronological order
            messages.reverse()

            # Format recent messages for context
            context_lines = []
            for msg in messages[:limit]:  # Last N messages
                msg_type = "Usuário" if msg['message_type'] == 'user' else "Assistente"
                context_lines.append(f"{msg_type}: {msg['content']}")

            return "Histórico da conversa:\n" + "\n".join(context_lines)

        except Exception as e:
            logger.error(f"Error getting chat context: {e}")
            return "Erro ao carregar histórico da conversa."

    def save_analysis_cache(self, cache_key: str, query_type: str, query_text: str, context_data: Dict[str, Any],
                           response_content: str, response_metadata: Dict[str, Any], expires_at: str,
                           session_id: Optional[str] = None, cached_at: Optional[str] = None) -> None:
        """Save analysis cache entry."""
        try:
            # Combine response_content and response_metadata into response_data JSONB
            response_data = {
                'response_content': response_content,
                'response_metadata': response_metadata,
                'query_text': query_text,
                'context_data': context_data,
                'session_id': session_id,
                'cached_at': cached_at or datetime.now().isoformat()
            }

            query = """
                INSERT INTO analysis_cache (cache_key, query_type, response_data, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cache_key)
                DO UPDATE SET
                    response_data = EXCLUDED.response_data,
                    expires_at = EXCLUDED.expires_at
            """
            self._execute_query(query, (cache_key, query_type, Json(response_data), expires_at), fetch=None)

        except Exception as e:
            logger.error(f"Error saving analysis cache: {e}")
            raise

    def get_analysis_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis if available and not expired."""
        try:
            query = """
                SELECT * FROM analysis_cache
                WHERE cache_key = %s AND expires_at > %s
            """
            result = self._execute_query(query, (cache_key, datetime.now().isoformat()), "one")

            if result:
                cache_entry = dict(result)
                # Extract data from response_data JSONB
                response_data = cache_entry.get('response_data', {})
                if response_data:
                    return {
                        'content': response_data.get('response_content', ''),
                        'metadata': response_data.get('response_metadata', {}),
                        'cached': True,
                        'query_text': response_data.get('query_text', ''),
                        'context_data': response_data.get('context_data', {}),
                        'cached_session_id': response_data.get('session_id'),
                        'cached_at': response_data.get('cached_at')
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting analysis cache: {e}")

        return None

    def get_chat_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat sessions."""
        try:
            query = """
                SELECT * FROM chat_sessions
                ORDER BY created_at DESC
                LIMIT %s
            """
            results = self._execute_query(query, (limit,), fetch="all")

            sessions = []
            for result in results:
                session = dict(result)
                # Get message count for this session
                count_query = "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = %s"
                count_result = self._execute_query(count_query, (session['id'],), "one")
                session['message_count'] = count_result['count'] if count_result else 0
                sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Error getting chat sessions: {e}")
            return []

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages."""
        try:
            # Messages will be deleted automatically due to CASCADE
            query = "DELETE FROM chat_sessions WHERE id = %s"
            result = self._execute_query(query, (session_id,), fetch=None)
            return result > 0

        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")
