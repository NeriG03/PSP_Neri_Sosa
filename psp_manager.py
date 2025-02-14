import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os

class PSPManager:
    def __init__(self):
        self.PREDEFINED_ACTIVITIES = [
            "planificacion", "analisis", "codificacion", 
            "pruebas", "lanzamiento", "revision de codigo", 
            "revision", "graficar", "codificar"
        ]
        self.projects = {}
        self.current_project = None
        self.current_activity = None
        self.start_time = None
        self.data_file = "psp_data.json"
        self.load_data()
        self.last_activity = None
        self.activity_history = set()
        self.pause_start_time = None
        self.current_pause_time = 0
        self.is_paused = False
        self.accumulated_pause_time = 0

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Convertir las listas de history back a sets
                    for project in data.values():
                        if 'activity_history' in project:
                            project['activity_history'] = set(project['activity_history'])
                    self.projects = data
        except json.JSONDecodeError:
            self.projects = {}
            print("Warning: Could not load data file. Starting fresh.")

    def save_data(self):
        # Convertir los sets a listas para serialización
        serializable_data = {}
        for project_name, project_data in self.projects.items():
            serializable_data[project_name] = {
                'activities': project_data['activities'],
                'activity_history': list(project_data['activity_history'])
            }
        
        with open(self.data_file, 'w') as f:
            json.dump(serializable_data, f)

    def create_project(self, name):
        if name not in self.projects:
            self.projects[name] = {
                'activities': [],
                'activity_history': set()
            }
        self.current_project = name
        self.activity_history = self.projects[name]['activity_history']

    def get_projects(self):
        return list(self.projects.keys())

    def start_activity(self, activity_name, comment=""):
        if not self.current_project:
            raise ValueError("No project selected")
        if self.current_activity:
            raise ValueError("An activity is already in progress")
        self.current_activity = activity_name
        self.current_comment = comment
        self.start_time = datetime.now()
        self.activity_history.add(activity_name)
        self.projects[self.current_project]['activity_history'] = self.activity_history

    def pause_activity(self):
        if self.current_activity and not self.is_paused:
            self.pause_start_time = datetime.now()
            self.is_paused = True

    def resume_from_pause(self):
        if self.is_paused and self.pause_start_time:
            pause_duration = self.get_pause_time()
            self.accumulated_pause_time += pause_duration
            self.pause_start_time = None
            self.is_paused = False
            return True
        return False

    def get_pause_time(self):
        if not self.pause_start_time:
            return 0
        return (datetime.now() - self.pause_start_time).total_seconds() / 60

    def stop_activity(self):
        if not self.start_time or not self.current_activity:
            return
        
        duration = self.get_elapsed_time()
        self.last_activity = self.current_activity
        self.projects[self.current_project]['activities'].append({
            'name': self.current_activity,
            'comment': self.current_comment,
            'duration': duration,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_data()
        self.current_activity = None
        self.current_comment = None
        self.start_time = None

    def finish_activity(self):
        if not self.start_time or not self.current_activity:
            return
        
        duration = self.get_elapsed_time()
        total_pause_time = self.accumulated_pause_time
        if self.is_paused and self.pause_start_time:
            total_pause_time += self.get_pause_time()

        self.projects[self.current_project]['activities'].append({
            'name': self.current_activity,
            'comment': self.current_comment,
            'duration': duration,
            'pause_time': total_pause_time,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_data()
        self.reset_activity_state()

    def reset_activity_state(self):
        self.current_activity = None
        self.current_comment = None
        self.start_time = None
        self.pause_start_time = None
        self.is_paused = False
        self.accumulated_pause_time = 0

    def get_elapsed_time(self):
        if not self.start_time:
            return 0
        return (datetime.now() - self.start_time).total_seconds() / 60

    def get_activity_history(self):
        if not self.current_project:
            return []
        return sorted(list(self.activity_history))

    def resume_activity(self, activity_name):
        if not self.current_activity:
            self.start_activity(activity_name)
            return True
        return False

    def get_project_summary(self, project_name):
        if project_name not in self.projects:
            return pd.DataFrame()
        
        activities = self.projects[project_name]['activities']
        return pd.DataFrame(activities)

    def plot_project_times(self, project_name):
        df = self.get_project_summary(project_name)
        if df.empty:
            return

        # Agrupar por tipo de actividad y sumar los tiempos
        grouped_df = df.groupby('name').agg({
            'duration': 'sum',
            'pause_time': 'sum'
        }).reset_index()

        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(grouped_df))
        width = 0.35

        # Crear las barras agrupadas
        ax.bar([i - width/2 for i in x], grouped_df['duration'], width, 
               label='Tiempo Total de Actividad', color='blue')
        ax.bar([i + width/2 for i in x], grouped_df['pause_time'], width, 
               label='Tiempo Total de Pausa', color='red')

        # Añadir etiquetas con los valores totales
        for i in x:
            # Etiqueta para tiempo de actividad
            ax.text(i - width/2, grouped_df['duration'].iloc[i], 
                   f'{grouped_df["duration"].iloc[i]:.1f}m', 
                   ha='center', va='bottom')
            # Etiqueta para tiempo de pausa
            ax.text(i + width/2, grouped_df['pause_time'].iloc[i], 
                   f'{grouped_df["pause_time"].iloc[i]:.1f}m', 
                   ha='center', va='bottom')

        plt.title(f'Distribución de Tiempos por Tipo de Actividad - {project_name}')
        plt.xlabel('Tipos de Actividades')
        plt.ylabel('Tiempo Total (minutos)')
        plt.xticks(x, grouped_df['name'], rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()
        
        return fig
