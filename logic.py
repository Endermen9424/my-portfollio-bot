import sqlite3
from config import DATABASE


skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Discord', 'Flask', 'HTML', 'CSS', 'C#', 'Unity'])]
statuses = [ (_,) for _ in (['Prototip Oluşturma', 'Geliştirme Aşamasında', 'Tamamlandı, kullanıma hazır', 'Güncellendi', 'Tamamlandı, ancak bakımı yapılmadı'])]

#DB_Manager sınıfı veritabanı işlemlerini yönetir
class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    #Tabloları başlangıçta oluşturmak için bu komut kullanılır eğer tablolar oluşturulduysa bu kodu çalıştırmayı atlayınız.
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            #projects tablosunu oluşturur
            conn.execute('''CREATE TABLE projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            partner_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''') 
            #skills tablosunu oluşturur
            conn.execute('''CREATE TABLE skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            #project_skills tablosunu oluşturur
            conn.execute('''CREATE TABLE project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            #status tablosunu oluşturur
            conn.execute('''CREATE TABLE status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            # Değişiklikleri kaydeder
            conn.commit()

    #Birden fazla veri eklemek için kullanılır sadece bu sınıf içinde kullanılır kullanmayınız
    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    #Veri seçmek için kullanılır sadece bu sınıf içinde kullanılır kullanmayınız
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    #Yukarıda oluşturulan listeler içindeki beceri ve durumları ekler
    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)

    #Yeni proje ekler
    def insert_project(self, data):
        sql = """INSERT INTO projects 
            (user_id, project_name, url, status_id) 
            values(?, ?, ?, ?)"""
        self.__executemany(sql, data)

    #Tek bir beceri ekler
    def insert_skill(self, user_id, project_name, skill):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    #Birden fazla beceri ekler
    def insert_skill_many(self, user_id, project_name, skills: list):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_ids = [self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0] for skill in skills]
        data = [(project_id, skill_id) for skill_id in skill_ids]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    #Tüm durumları getirir
    def get_statuses(self):
        sql="SELECT status_name from status"
        return self.__select_data(sql)
        
    #Durum adına göre durum id'sini getirir
    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    #Kullanıcının tüm projelerini getirir
    def get_projects(self, user_id):
        sql="""SELECT * FROM projects 
            WHERE user_id = ?"""
        return self.__select_data(sql, data = (user_id,))
        
    #Proje adına ve kullanıcı id'sine göre proje id'sini getirir
    def get_project_id(self, project_name, user_id):
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]

    #Tüm becerileri getirir  
    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')
    
    #Proje adına göre o projeye ait becerileri getirir
    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
            JOIN project_skills ON projects.project_id = project_skills.project_id 
            JOIN skills ON skills.skill_id = project_skills.skill_id 
            WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    #Kullanıcı id'si ve proje adına göre o projeye ait bilgileri getirir
    def get_project_info(self, user_id, project_name):
        sql = """
            SELECT project_name, description, url, status_name FROM projects 
            JOIN status ON
            status.status_id = projects.status_id
            WHERE project_name=? AND user_id=?
            """
        return self.__select_data(sql=sql, data = (project_name, user_id))

    #Proje bilgilerini günceller
    def update_projects(self, param, data):
        sql = f"""UPDATE projects SET {param} = ? 
            WHERE project_name = ? AND user_id = ?"""
        self.__executemany(sql, [data]) 

    #Proje veya beceri silme işlemleri
    def delete_project(self, user_id, project_id):
        sql = """DELETE FROM projects 
            WHERE user_id = ? AND project_id = ? """
        self.__executemany(sql, [(user_id, project_id)])
    
    #Project id ve skill id'ye göre beceriyi siler
    def delete_skill(self, project_id, skill_id):
        sql = """DELETE FROM skills 
            WHERE skill_id = ? AND project_id = ? """
        self.__executemany(sql, [(skill_id, project_id)])

    #Tüm tabloları temizler
    def clear_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("DELETE FROM skills")
            conn.execute("DELETE FROM status")
            conn.execute("DELETE FROM projects")
            conn.execute("DELETE FROM project_skills")
            conn.commit()



if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.clear_tables()
    manager.default_insert()

    manager.insert_project([(1, "MyHackatohnProject", "https://github.com/Endermen9424/MyHackatohnProject", 3),
                            (1, "Night-Watchman", "https://github.com/Endermen9424/Night-Watchman", 3)])

    manager.insert_skill_many(1, "MyHackatohnProject", ["Python", "Flask", "HTML", "CSS"])
    manager.insert_skill(1, "Night-Watchman", "Unity")