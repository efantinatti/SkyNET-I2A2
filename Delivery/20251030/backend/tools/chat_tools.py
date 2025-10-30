"""
Chat tools for document and CSV analysis.

These tools provide structured access to document data and CSV analysis
for the chat agent to use when answering questions.
"""
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentAnalysisTool:
    """Tool for analyzing fiscal documents."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def get_document_summary(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get summary and insights for a specific document."""

        try:
            # Get document
            doc_result = self.supabase.table('fiscal_documents').select('*').eq(
                'id', document_id
            ).execute()

            if not doc_result.data:
                return None

            document = doc_result.data[0]

            # Get summary
            summary_result = self.supabase.table('document_summaries').select('*').eq(
                'fiscal_document_id', document_id
            ).execute()

            summary = summary_result.data[0] if summary_result.data else None

            # Get insights
            insights_result = self.supabase.table('analysis_insights').select('*').eq(
                'fiscal_document_id', document_id
            ).execute()

            insights = insights_result.data if insights_result.data else []

            return {
                'document': document,
                'summary': summary,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error getting document summary: {e}")
            return None

    def get_documents_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get documents matching specific criteria."""

        try:
            query = self.supabase.table('fiscal_documents').select('*')

            # Apply filters
            if criteria.get('document_type'):
                query = query.eq('document_type', criteria['document_type'])

            if criteria.get('issuer_cnpj'):
                query = query.eq('issuer_cnpj', criteria['issuer_cnpj'])

            if criteria.get('date_from'):
                query = query.gte('created_at', criteria['date_from'])

            if criteria.get('date_to'):
                query = query.lte('created_at', criteria['date_to'])

            if criteria.get('validation_status'):
                query = query.eq('validation_status', criteria['validation_status'])

            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting documents by criteria: {e}")
            return []

    def analyze_financial_impact(self, document_ids: List[str]) -> Dict[str, Any]:
        """Analyze the financial impact of a set of documents."""

        try:
            # Get documents
            result = self.supabase.table('fiscal_documents').select('*').in_(
                'id', document_ids
            ).execute()

            documents = result.data if result.data else []

            total_value = 0
            tax_totals = {'ICMS': 0, 'IPI': 0, 'PIS': 0, 'COFINS': 0}
            document_types = {}
            issuers = {}

            for doc in documents:
                data = doc.get('extracted_data', {})

                # Sum total values
                if data.get('total'):
                    total_value += float(data['total'])

                # Sum taxes
                if data.get('impostos'):
                    for tax, value in data['impostos'].items():
                        if tax in tax_totals and value:
                            tax_totals[tax] += float(value)

                # Count document types
                doc_type = doc.get('document_type', 'Unknown')
                document_types[doc_type] = document_types.get(doc_type, 0) + 1

                # Count issuers
                issuer_cnpj = doc.get('issuer_cnpj', 'Unknown')
                issuers[issuer_cnpj] = issuers.get(issuer_cnpj, 0) + 1

            return {
                'total_documents': len(documents),
                'total_value': total_value,
                'tax_summary': tax_totals,
                'document_types': document_types,
                'top_issuers': dict(list(issuers.items())[:5])  # Top 5 issuers
            }

        except Exception as e:
            logger.error(f"Error analyzing financial impact: {e}")
            return {}


class CSVAnalysisTool:
    """Tool for analyzing CSV data."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def get_csv_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific CSV analysis."""

        try:
            result = self.supabase.table('analyses').select('*').eq(
                'id', analysis_id
            ).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting CSV analysis: {e}")
            return None

    def analyze_csv_data(self, csv_data: str) -> Dict[str, Any]:
        """Analyze CSV data and extract insights."""

        try:
            # Parse CSV data
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return {'error': 'CSV data must have at least header and one data row'}

            # Parse header
            headers = [h.strip().strip('"') for h in lines[0].split(',')]

            # Parse data rows
            data_rows = []
            for line in lines[1:]:
                if line.strip():  # Skip empty lines
                    values = [v.strip().strip('"') for v in line.split(',')]
                    if len(values) == len(headers):
                        data_rows.append(values)

            if not data_rows:
                return {'error': 'No valid data rows found in CSV'}

            # Convert to DataFrame for analysis
            df = pd.DataFrame(data_rows, columns=headers)

            # Basic statistics
            stats = {}
            numeric_columns = df.select_dtypes(include=['number']).columns

            for col in numeric_columns:
                try:
                    stats[col] = {
                        'count': int(df[col].count()),
                        'mean': float(df[col].mean()),
                        'median': float(df[col].median()),
                        'std': float(df[col].std()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'sum': float(df[col].sum())
                    }
                except Exception as e:
                    logger.warning(f"Error calculating stats for column {col}: {e}")

            # Categorical analysis
            categorical_columns = df.select_dtypes(include=['object']).columns
            categorical_stats = {}

            for col in categorical_columns:
                value_counts = df[col].value_counts()
                categorical_stats[col] = {
                    'unique_count': int(value_counts.count()),
                    'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                    'most_common_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    'top_5_values': value_counts.head(5).to_dict()
                }

            # Detect potential issues
            issues = []

            # Check for missing values
            missing_pct = (df.isnull().sum() / len(df)) * 100
            for col, pct in missing_pct.items():
                if pct > 50:
                    issues.append(f"Column '{col}' has {pct:.1f}% missing values")

            # Check for outliers in numeric columns
            for col in numeric_columns:
                try:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                    if len(outliers) > 0:
                        issues.append(f"Column '{col}' has {len(outliers)} potential outliers")
                except Exception as e:
                    logger.warning(f"Error detecting outliers in column {col}: {e}")

            return {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': headers,
                'numeric_columns': list(numeric_columns),
                'categorical_columns': list(categorical_columns),
                'statistics': stats,
                'categorical_analysis': categorical_stats,
                'data_preview': df.head(5).to_dict('records'),
                'issues': issues,
                'summary': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'numeric_columns': len(numeric_columns),
                    'categorical_columns': len(categorical_columns),
                    'potential_issues': len(issues)
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing CSV data: {e}")
            return {'error': f'Failed to analyze CSV data: {str(e)}'}


class InsightGenerator:
    """Generate insights from document and CSV analysis."""

    def __init__(self, document_tool: DocumentAnalysisTool, csv_tool: CSVAnalysisTool):
        self.document_tool = document_tool
        self.csv_tool = csv_tool

    def generate_financial_insights(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Generate financial insights from documents."""

        insights = []

        if not documents:
            return insights

        # Total value analysis
        total_value = sum(float(doc.get('extracted_data', {}).get('total', 0)) for doc in documents)
        insights.append(f"Total de documentos analisados: {len(documents)}")
        insights.append(f"Valor total dos documentos: R$ {total_value:,.2f}")

        # Document type distribution
        doc_types = {}
        for doc in documents:
            doc_type = doc.get('document_type', 'Unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        if doc_types:
            insights.append("Distribuição por tipo de documento:")
            for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
                insights.append(f"  - {doc_type}: {count} documentos")

        # Tax analysis
        tax_totals = {}
        for doc in documents:
            taxes = doc.get('extracted_data', {}).get('impostos', {})
            for tax, value in taxes.items():
                if value:
                    tax_totals[tax] = tax_totals.get(tax, 0) + float(value)

        if tax_totals:
            insights.append("Resumo de impostos:")
            for tax, total in sorted(tax_totals.items(), key=lambda x: x[1], reverse=True):
                insights.append(f"  - {tax}: R$ {total:.2f}")

        # Validation status
        validation_stats = {}
        for doc in documents:
            status = doc.get('validation_status', 'unknown')
            validation_stats[status] = validation_stats.get(status, 0) + 1

        if validation_stats:
            insights.append("Status de validação:")
            for status, count in validation_stats.items():
                insights.append(f"  - {status}: {count} documentos")

        return insights

    def generate_csv_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from CSV analysis."""

        insights = []

        if 'error' in analysis:
            return [f"Erro na análise: {analysis['error']}"]

        summary = analysis.get('summary', {})
        insights.append(f"Análise de CSV com {summary.get('total_rows', 0)} linhas e {summary.get('total_columns', 0)} colunas")

        # Numeric column insights
        numeric_cols = analysis.get('numeric_columns', [])
        if numeric_cols:
            insights.append(f"Colunas numéricas identificadas: {', '.join(numeric_cols)}")

            stats = analysis.get('statistics', {})
            for col in numeric_cols:
                if col in stats:
                    col_stats = stats[col]
                    insights.append(f"  - {col}: média={col_stats['mean']:.2f}, min={col_stats['min']:.2f}, max={col_stats['max']:.2f}, total={col_stats['sum']:.2f}")
        # Categorical column insights
        categorical_cols = analysis.get('categorical_columns', [])
        if categorical_cols:
            insights.append(f"Colunas categóricas identificadas: {', '.join(categorical_cols)}")

            cat_analysis = analysis.get('categorical_analysis', {})
            for col in categorical_cols:
                if col in cat_analysis:
                    col_analysis = cat_analysis[col]
                    insights.append(f"  - {col}: {col_analysis['unique_count']} valores únicos, mais comum: {col_analysis['most_common']} ({col_analysis['most_common_count']} ocorrências)")

        # Issues
        issues = analysis.get('issues', [])
        if issues:
            insights.append("Problemas identificados:")
            for issue in issues:
                insights.append(f"  - {issue}")

        return insights
