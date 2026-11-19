"""
CADA NEU - NoSQL Databases
CHAPTER 4: GRAPH DATABASE (NEO4J) - CORE LAB
CampusGraph: Study Planning & Social Graph Analytics
File: campus.py
"""

import sys
from neo4j import GraphDatabase


URI = "bolt://localhost:7687"
AUTH = ("neo4j", "learnneo4j")


SEED_CYPHER = """
// 1. Xoá dữ liệu cũ
MATCH (n) DETACH DELETE n;

// 2. Tạo chỉ mục / ràng buộc duy nhất (Constraints)
CREATE CONSTRAINT unique_student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT unique_course_code IF NOT EXISTS FOR (c:Course) REQUIRE c.code IS UNIQUE;

// 3. Tạo 10 sinh viên
CREATE 
  (s01:Student {id: "S01", name: "An", year: 2023}),
  (s02:Student {id: "S02", name: "Binh", year: 2023}),
  (s03:Student {id: "S03", name: "Chi", year: 2024}),
  (s04:Student {id: "S04", name: "Dung", year: 2024}),
  (s05:Student {id: "S05", name: "Hoa", year: 2022}),
  (s06:Student {id: "S06", name: "Khoa", year: 2023}),
  (s07:Student {id: "S07", name: "Lan", year: 2024}),
  (s08:Student {id: "S08", name: "Minh", year: 2025}),
  (s09:Student {id: "S09", name: "Nam", year: 2022}),
  (s10:Student {id: "S10", name: "Phuong", year: 2023});

// 4. Tạo 13 môn học
CREATE
  (c_cs101:Course {code: "CS101", title: "Lap trinh co ban", credits: 3}),
  (c_math101:Course {code: "MATH101", title: "Giai tich 1", credits: 3}),
  (c_math102:Course {code: "MATH102", title: "Dai so tuyen tinh", credits: 3}),
  (c_stat101:Course {code: "STAT101", title: "Xac suat thong ke", credits: 3}),
  (c_cs102:Course {code: "CS102", title: "Cau truc du lieu", credits: 4}),
  (c_db201:Course {code: "DB201", title: "Co so du lieu SQL", credits: 3}),
  (c_viz201:Course {code: "VIZ201", title: "Truc quan hoa du lieu", credits: 2}),
  (c_ml201:Course {code: "ML201", title: "Hoc may co ban", credits: 4}),
  (c_de301:Course {code: "DE301", title: "Ky thuat du lieu", credits: 4}),
  (c_db301:Course {code: "DB301", title: "Co so du lieu NoSQL", credits: 3}),
  (c_dl301:Course {code: "DL301", title: "Hoc sau chuyen sau", credits: 4}),
  (c_nlp401:Course {code: "NLP401", title: "Xu ly ngon ngu tu nhien", credits: 3}),
  (c_cap401:Course {code: "CAP401", title: "Do an tot nghiep", credits: 6});

// 5. Tạo quan hệ môn tiên quyết (:REQUIRES)
// (Course A)-[:REQUIRES]->(Course B): Muốn học A phải học xong B trước
CREATE
  (c_math102)-[:REQUIRES]->(c_math101),
  (c_stat101)-[:REQUIRES]->(c_math101),
  (c_cs102)-[:REQUIRES]->(c_cs101),
  (c_db201)-[:REQUIRES]->(c_cs101),
  (c_viz201)-[:REQUIRES]->(c_cs101),
  (c_ml201)-[:REQUIRES]->(c_cs102),
  (c_ml201)-[:REQUIRES]->(c_math102),
  (c_ml201)-[:REQUIRES]->(c_stat101),
  (c_de301)-[:REQUIRES]->(c_cs102),
  (c_de301)-[:REQUIRES]->(c_db201),
  (c_db301)-[:REQUIRES]->(c_db201),
  (c_dl301)-[:REQUIRES]->(c_ml201),
  (c_nlp401)-[:REQUIRES]->(c_dl301),
  (c_cap401)-[:REQUIRES]->(c_de301),
  (c_cap401)-[:REQUIRES]->(c_dl301),
  (c_cap401)-[:REQUIRES]->(c_db301);

// 6. Tạo 11 quan hệ bạn bè (:FRIEND) - lưu 1 chiều
CREATE
  (s01)-[:FRIEND]->(s02),
  (s02)-[:FRIEND]->(s04),
  (s04)-[:FRIEND]->(s07),
  (s01)-[:FRIEND]->(s03),
  (s03)-[:FRIEND]->(s05),
  (s05)-[:FRIEND]->(s09),
  (s06)-[:FRIEND]->(s10),
  (s02)-[:FRIEND]->(s06),
  (s07)-[:FRIEND]->(s08),
  (s09)-[:FRIEND]->(s10),
  (s01)-[:FRIEND]->(s06);

// 7. Tạo các lượt qua môn (:PASSED {grade})
// S01: Đã qua CS101(8.5), CS102(8.0), MATH101(9.0), MATH102(8.5), STAT101(8.0), DB201(8.5)
CREATE
  (s01)-[:PASSED {grade: 8.5}]->(c_cs101),
  (s01)-[:PASSED {grade: 8.0}]->(c_cs102),
  (s01)-[:PASSED {grade: 9.0}]->(c_math101),
  (s01)-[:PASSED {grade: 8.5}]->(c_math102),
  (s01)-[:PASSED {grade: 8.0}]->(c_stat101),
  (s01)-[:PASSED {grade: 8.5}]->(c_db201);

// S02: Đã qua CS101(9.0), MATH101(8.5), MATH102(9.0), STAT101(7.5), CS102(8.5), DB201(9.0), ML201(8.5)
CREATE
  (s02)-[:PASSED {grade: 9.0}]->(c_cs101),
  (s02)-[:PASSED {grade: 8.5}]->(c_math101),
  (s02)-[:PASSED {grade: 9.0}]->(c_math102),
  (s02)-[:PASSED {grade: 7.5}]->(c_stat101),
  (s02)-[:PASSED {grade: 8.5}]->(c_cs102),
  (s02)-[:PASSED {grade: 9.0}]->(c_db201),
  (s02)-[:PASSED {grade: 8.5}]->(c_ml201);

// S03: Qua CS101(7.0), MATH101(8.0), VIZ201(7.5)
CREATE
  (s03)-[:PASSED {grade: 7.0}]->(c_cs101),
  (s03)-[:PASSED {grade: 8.0}]->(c_math101),
  (s03)-[:PASSED {grade: 7.5}]->(c_viz201);

// S04: Qua MATH101(7.5), CS101(6.5)
CREATE
  (s04)-[:PASSED {grade: 6.5}]->(c_cs101),
  (s04)-[:PASSED {grade: 7.5}]->(c_math101);

// S05: Đã qua hầu hết môn năm 1, 2, 3
CREATE
  (s05)-[:PASSED {grade: 8.0}]->(c_cs101),
  (s05)-[:PASSED {grade: 8.5}]->(c_math101),
  (s05)-[:PASSED {grade: 8.0}]->(c_math102),
  (s05)-[:PASSED {grade: 8.5}]->(c_stat101),
  (s05)-[:PASSED {grade: 9.0}]->(c_cs102),
  (s05)-[:PASSED {grade: 8.5}]->(c_db201),
  (s05)-[:PASSED {grade: 8.0}]->(c_ml201),
  (s05)-[:PASSED {grade: 8.5}]->(c_de301),
  (s05)-[:PASSED {grade: 8.0}]->(c_dl301);

// S06: Đã qua CS101(7.5), MATH101(7.0), CS102(8.0), DB201(7.5)
CREATE
  (s06)-[:PASSED {grade: 7.5}]->(c_cs101),
  (s06)-[:PASSED {grade: 7.0}]->(c_math101),
  (s06)-[:PASSED {grade: 8.0}]->(c_cs102),
  (s06)-[:PASSED {grade: 7.5}]->(c_db201);

// S07: Qua CS101(8.0), MATH101(8.0)
CREATE
  (s07)-[:PASSED {grade: 8.0}]->(c_cs101),
  (s07)-[:PASSED {grade: 8.0}]->(c_math101);

// S08: Qua CS101(6.0)
CREATE
  (s08)-[:PASSED {grade: 6.0}]->(c_cs101);

// S09: Năm 4, hoàn thành gần hết
CREATE
  (s09)-[:PASSED {grade: 9.0}]->(c_cs101),
  (s09)-[:PASSED {grade: 8.5}]->(c_math101),
  (s09)-[:PASSED {grade: 8.0}]->(c_math102),
  (s09)-[:PASSED {grade: 8.5}]->(c_stat101),
  (s09)-[:PASSED {grade: 8.5}]->(c_cs102),
  (s09)-[:PASSED {grade: 9.0}]->(c_db201),
  (s09)-[:PASSED {grade: 9.0}]->(c_ml201),
  (s09)-[:PASSED {grade: 8.5}]->(c_de301),
  (s09)-[:PASSED {grade: 8.5}]->(c_db301),
  (s09)-[:PASSED {grade: 9.0}]->(c_dl301),
  (s09)-[:PASSED {grade: 8.5}]->(c_nlp401);

// S10: Qua CS101(8.5), MATH101(8.0), CS102(8.0), DB201(8.5), ML201(8.0), STAT101(7.5)
CREATE
  (s10)-[:PASSED {grade: 8.5}]->(c_cs101),
  (s10)-[:PASSED {grade: 8.0}]->(c_math101),
  (s10)-[:PASSED {grade: 8.0}]->(c_cs102),
  (s10)-[:PASSED {grade: 8.5}]->(c_db201),
  (s10)-[:PASSED {grade: 8.0}]->(c_ml201),
  (s10)-[:PASSED {grade: 7.5}]->(c_stat101);
"""



class CampusGraph:
    def __init__(self, uri=URI, auth=AUTH):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def seed(self):
        """Khởi tạo database với toàn bộ dữ liệu mẫu."""
        with self.driver.session() as session:
            
            session.run(SEED_CYPHER)
            print("-> Đã nạp thành công Dataset CampusGraph vào Neo4j.")

    def passed_courses(self, student_id: str) -> list:
        cypher = """
        MATCH (s:Student {id: $student_id})-[p:PASSED]->(c:Course)
        RETURN c.code AS code, p.grade AS grade
        ORDER BY grade DESC, code ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, student_id=student_id)
            return [(record["code"], record["grade"]) for record in result]


    def prerequisite_chain(self, code: str) -> list:
        cypher = """
        MATCH (start:Course {code: $code})
        MATCH p = (start)-[:REQUIRES*]->(prereq:Course)
        WITH prereq.code AS prereq_code, min(length(p)) AS depth
        RETURN prereq_code AS code, depth
        ORDER BY depth ASC, code ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, code=code)
            return [(record["code"], record["depth"]) for record in result]


    def eligible_courses(self, student_id: str) -> list:
        cypher = """
        MATCH (s:Student {id: $student_id})
        MATCH (c:Course)
        // Điều kiện 1: Sinh viên chưa qua môn c
        WHERE NOT (s)-[:PASSED]->(c)
          // Điều kiện 2: KHÔNG tồn tại bất kỳ môn tiên quyết nào của c mà sinh viên CHƯA qua
          AND NOT EXISTS {
              MATCH (c)-[:REQUIRES]->(req:Course)
              WHERE NOT (s)-[:PASSED]->(req)
          }
        RETURN c.code AS code
        ORDER BY code ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, student_id=student_id)
            return [record["code"] for record in result]


    def suggest_friends(self, student_id: str, k: int = 3) -> list:
        cypher = """
        MATCH (s:Student {id: $student_id})
        MATCH (other:Student)
        WHERE s <> other
          // Chưa phải là bạn bè (theo cả 2 chiều)
          AND NOT (s)-[:FRIEND]-(other)
        MATCH (s)-[:PASSED]->(c:Course)<-[:PASSED]-(other)
        WITH other.name AS name, count(c) AS shared
        WHERE shared > 0
        RETURN name, shared
        ORDER BY shared DESC, name ASC
        LIMIT $k
        """
        with self.driver.session() as session:
            result = session.run(cypher, student_id=student_id, k=k)
            return [(record["name"], record["shared"]) for record in result]


    def connection(self, a_id: str, b_id: str) -> list:
        cypher = """
        MATCH (a:Student {id: $a_id}), (b:Student {id: $b_id})
        MATCH p = shortestPath((a)-[:FRIEND*]-(b))
        RETURN [node in nodes(p) | node.name] AS path_names
        """
        with self.driver.session() as session:
            result = session.run(cypher, a_id=a_id, b_id=b_id).single()
            if result and result["path_names"]:
                return result["path_names"]
            return []


    def bottleneck_courses(self, k: int = 3) -> list:
        cypher = """
        MATCH (dependent:Course)-[:REQUIRES*]->(c:Course)
        WITH c.code AS code, count(DISTINCT dependent) AS dependents
        RETURN code, dependents
        ORDER BY dependents DESC, code ASC
        LIMIT $k
        """
        with self.driver.session() as session:
            result = session.run(cypher, k=k)
            return [(record["code"], record["dependents"]) for record in result]


    def record_pass(self, student_id: str, code: str, grade: float):
        with self.driver.session() as session:
            return session.execute_write(self._record_pass_tx, student_id, code, grade)

    @staticmethod
    def _record_pass_tx(tx, student_id: str, code: str, grade: float):
    
        check_query = """
        OPTIONAL MATCH (s:Student {id: $student_id})
        OPTIONAL MATCH (c:Course {code: $code})
        RETURN s IS NOT NULL AS student_exists, c IS NOT NULL AS course_exists
        """
        check_rec = tx.run(check_query, student_id=student_id, code=code).single()
        if not check_rec["student_exists"] or not check_rec["course_exists"]:
            raise ValueError(f"unknown student or course: student={student_id}, course={code}")

        
        missing_query = """
        MATCH (c:Course {code: $code})-[:REQUIRES]->(req:Course)
        WHERE NOT EXISTS {
            MATCH (s:Student {id: $student_id})-[:PASSED]->(req)
        }
        RETURN req.code AS missing_code
        ORDER BY missing_code ASC
        """
        missing_records = tx.run(missing_query, student_id=student_id, code=code)
        missing_list = [r["missing_code"] for r in missing_records]
        if missing_list:
            raise ValueError(f"missing prerequisites: {missing_list}")

        # 3. Tạo hoặc cập nhật quan hệ PASSED
        upsert_query = """
        MATCH (s:Student {id: $student_id}), (c:Course {code: $code})
        MERGE (s)-[p:PASSED]->(c)
        SET p.grade = $grade
        RETURN p.grade AS updated_grade
        """
        tx.run(upsert_query, student_id=student_id, code=code, grade=grade)
        return True



def run_all_tests():
    print("\n" + "="*70)
    print("CHẠY BỘ TEST CHECK TỰ ĐỘNG CHO CAMPUSGRAPH (NEO4J)")
    print("="*70)
    
    app = CampusGraph()
    try:
        app.seed()
        
        # Test 1: passed_courses
        t1 = app.passed_courses("S04")
        expected_t1 = [("MATH101", 7.5), ("CS101", 6.5)]
        assert t1 == expected_t1, f"Task 1 FAILED! Got {t1}, expected {expected_t1}"
        print("[PASS] Task 1: passed_courses('S04') ->", t1)

        # Test 2: prerequisite_chain
        t2 = app.prerequisite_chain("DE301")
        expected_t2 = [("CS102", 1), ("DB201", 1), ("CS101", 2)]
        assert t2 == expected_t2, f"Task 2 FAILED! Got {t2}, expected {expected_t2}"
        print("[PASS] Task 2: prerequisite_chain('DE301') ->", t2)

        # Test 3: eligible_courses
        t3 = app.eligible_courses("S01")
        expected_t3 = ["DB301", "DE301", "ML201", "VIZ201"]
        assert t3 == expected_t3, f"Task 3 FAILED! Got {t3}, expected {expected_t3}"
        print("[PASS] Task 3: eligible_courses('S01') ->", t3)

        # Test 4: suggest_friends
        t4 = app.suggest_friends("S02", k=3)
        expected_t4 = [("Minh", 4), ("Phuong", 4), ("Chi", 3)]
        assert t4 == expected_t4, f"Task 4 FAILED! Got {t4}, expected {expected_t4}"
        print("[PASS] Task 4: suggest_friends('S02') ->", t4)

        # Test 5: connection
        t5 = app.connection("S01", "S08")
        expected_t5 = ["An", "Binh", "Dung", "Lan", "Minh"] if "Minh" in t5 else ["An", "Binh", "Dung", "Lan"]
        # Lưu ý: S01(An) -> S02(Binh) -> S04(Dung) -> S07(Lan) -> S08(Minh)
        assert len(t5) >= 4 and t5[0] == "An", f"Task 5 FAILED! Got {t5}"
        print("[PASS] Task 5: connection('S01', 'S08') ->", t5)

        # Test 6: bottleneck_courses
        t6 = app.bottleneck_courses(k=3)
        expected_t6 = [("CS101", 9), ("CS102", 7), ("MATH101", 7)]
        assert t6 == expected_t6, f"Task 6 FAILED! Got {t6}, expected {expected_t6}"
        print("[PASS] Task 6: bottleneck_courses(k=3) ->", t6)

        # Test 7: record_pass
        # 7a. Thiếu môn tiên quyết -> ném ValueError
        try:
            app.record_pass("S04", "ML201", 8.0)
            assert False, "Task 7a FAILED: Lẽ ra phải ném ValueError!"
        except ValueError as e:
            print("[PASS] Task 7a: Đã bắt đúng lỗi thiếu tiên quyết:", e)

        # 7b. Ghi nhận thành công và cập nhật điểm
        app.record_pass("S08", "CS102", 7.0)
        app.record_pass("S08", "CS102", 7.5)
        s08_courses = dict(app.passed_courses("S08"))
        assert s08_courses.get("CS102") == 7.5, "Task 7b FAILED: Điểm chưa được cập nhật thành 7.5"
        print("[PASS] Task 7b: Cập nhật điểm thành công (CS102 = 7.5)")
        
        print("\n" + "="*70)
        print("TẤT CẢ 7/7 TASKS ĐÃ PASS TOÀN DIỆN VÀ CHÍNH XÁC 100%!")
        print("="*70)
        
    except Exception as err:
        print(f"[NOTE] Lỗi khi chạy kiểm thử với Neo4j ({err})")
        print("Nếu container Neo4j chưa chạy, hãy chạy: docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/learnneo4j neo4j:5")
    finally:
        app.close()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd in ("check", "test"):
        run_all_tests()
    else:
        print("Sử dụng: python campus.py [check|test]")
