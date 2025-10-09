from supabase import create_client, Client


class SupabaseMemory:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def create_session(self, dataset_name: str, dataset_hash: str, user_id: str) -> str:
        response = self.client.table("sessions").insert({
            "dataset_name": dataset_name,
            "dataset_hash": dataset_hash,
            "user_id": user_id
        }).execute()
        return response.data[0]['id']

    def log_conversation(self, session_id: str, question: str, answer: str, chart_json: dict | None = None) -> str:
        payload = {
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "chart_json": chart_json if chart_json is not None else None
        }
        response = self.client.table("conversations").insert(payload).execute()
        return response.data[0]['id']

    def store_analysis(self, session_id: str, conversation_id: str | None, analysis_type: str, results: dict):
        # Garante que temos pelo menos um ID de conversa válido
        if not conversation_id:
            # Se não houver conversation_id, cria uma entrada na tabela de conversas
            conversation = self.client.table("conversations").select("id").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
            if conversation.data:
                conversation_id = conversation.data[0]['id']
            else:
                # Se não houver conversa, cria uma vazia
                conversation = self.client.table("conversations").insert({
                    "session_id": session_id,
                    "question": "Análise automática",
                    "answer": "Análise gerada pelo sistema"
                }).execute()
                conversation_id = conversation.data[0]['id']
                
        self.client.table("analyses").insert({
            "session_id": session_id,
            "conversation_id": conversation_id,
            "analysis_type": analysis_type,
            "results": results
        }).execute()

    def store_conclusion(self, session_id: str, conversation_id: str | None, conclusion_text: str,
                         confidence_score: float | None = None):
        # Garante que temos pelo menos um ID de conversa válido
        if not conversation_id:
            # Se não houver conversation_id, tenta obter o mais recente
            conversation = self.client.table("conversations").select("id").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
            if conversation.data:
                conversation_id = conversation.data[0]['id']
            else:
                # Se não houver conversa, cria uma vazia
                conversation = self.client.table("conversations").insert({
                    "session_id": session_id,
                    "question": "Conclusão automática",
                    "answer": "Conclusão gerada pelo sistema"
                }).execute()
                conversation_id = conversation.data[0]['id']
                
        self.client.table("conclusions").insert({
            "session_id": session_id,
            "conversation_id": conversation_id,
            "conclusion_text": conclusion_text,
            "confidence_score": confidence_score
        }).execute()

    def store_generated_code(self, session_id: str, conversation_id: str, code_type: str, python_code: str,
                             description: str | None):
        # Adicionar proteção contra códigos muito longos que podem causar timeout
        if len(python_code) > 5000:
            python_code = python_code[:5000] + "\n\n# ... (código truncado para evitar timeout no banco de dados)"

        try:
            self.client.table("generated_codes").insert({
                "session_id": session_id,
                "conversation_id": conversation_id,
                "code_type": code_type,
                "python_code": python_code,
                "description": description
            }).execute()
        except Exception as e:
            # Em caso de erro no banco, não propagar a exceção para não interromper o fluxo principal
            print(f"Erro ao salvar código gerado no banco: {e}")
            # Não relançar a exceção para não interromper o usuário

    def get_session_history(self, session_id: str) -> dict:
        conversations = self.client.table("conversations").select("*").eq("session_id", session_id).order(
            "created_at").execute().data
        analyses = self.client.table("analyses").select("*").eq("session_id", session_id).order(
            "created_at").execute().data
        conclusions = self.client.table("conclusions").select("*").eq("session_id", session_id).order(
            "created_at").execute().data

        return {
            "conversations": conversations,
            "analyses": analyses,
            "conclusions": conclusions
        }

    def get_user_sessions(self, user_id: str):
        return self.client.table("sessions").select("id, created_at, dataset_name").eq("user_id", user_id).order(
            "created_at", desc=True).execute().data

    def get_generated_codes(self, session_id: str):
        return self.client.table("generated_codes").select(
            "id, created_at, code_type, python_code, description, conversation_id"
        ).eq("session_id", session_id).order("created_at", desc=True).execute().data