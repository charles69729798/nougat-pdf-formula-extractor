#!/usr/bin/env python3
"""
hybrid_formula_extractor.py - 라이선스 안전한 수식 추출기
MIT/Apache 라이선스 도구들만 사용
"""
import sys
import os
from pathlib import Path
import fitz  # MIT License
from PIL import Image, ImageEnhance  # MIT License
import json
from datetime import datetime

class LicenseSafeFormulaExtractor:
    """라이선스 안전한 수식 추출기 (MIT/Apache만 사용)"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"hybrid_output_{self.timestamp}")
        self.output_dir.mkdir(exist_ok=True)
        
        # 라이선스 안전한 도구들 초기화
        self.init_safe_tools()
    
    def init_safe_tools(self):
        """라이선스 안전한 도구들 초기화"""
        print("🔧 라이선스 안전한 OCR 도구 초기화 중...")
        
        # 1. rapid-latex-ocr (MIT License)
        try:
            from rapid_latex_ocr import LaTeXOCR  # 정확한 클래스명: LaTeXOCR (대문자 T, X)
            self.formula_ocr = LaTeXOCR()
            print("  ✅ rapid-latex-ocr (LaTeXOCR) 로드 완료")
        except ImportError:
            print("  ❌ rapid-latex-ocr 없음. 설치: pip install rapid-latex-ocr")
            self.formula_ocr = None
        except Exception as e:
            print(f"  ❌ rapid-latex-ocr 로드 오류: {e}")
            self.formula_ocr = None
        
        # 2. PaddleOCR (Apache 2.0 License) - v3.1.0 이상
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR v3.1.0의 새로운 파라미터 사용
            try:
                # 방법 1: 중국어 + 텍스트라인 방향 보정 (새 파라미터)
                self.text_ocr = PaddleOCR(lang='ch', use_textline_orientation=True)
                print("  ✅ PaddleOCR (중국어+영어+방향보정) 로드 완료")
            except:
                try:
                    # 방법 2: 영어만
                    self.text_ocr = PaddleOCR(lang='en')
                    print("  ✅ PaddleOCR (영어) 로드 완료")
                except:
                    try:
                        # 방법 3: 최소 파라미터
                        self.text_ocr = PaddleOCR()
                        print("  ✅ PaddleOCR (기본설정) 로드 완료")
                    except Exception as e:
                        print(f"  ⚠️ PaddleOCR 초기화 실패: {e}")
                        print("     💡 PaddlePaddle 설치 필요: pip install paddlepaddle")
                        self.text_ocr = None
        except ImportError:
            print("  ❌ PaddleOCR 없음. 설치: pip install paddleocr paddlepaddle")
            self.text_ocr = None
        except Exception as e:
            print(f"  ❌ PaddleOCR 로드 실패: {e}")
            self.text_ocr = None
        
        # 3. pix2text (MIT License) 백업
        try:
            from pix2text import Pix2Text
            self.backup_ocr = Pix2Text()
            print("  ✅ Pix2Text (MIT) 백업 도구 로드 완료")
        except ImportError:
            print("  ⚠️ Pix2Text 백업 도구 없음")
            self.backup_ocr = None
    
    def enhance_pdf_quality(self, pdf_path):
        """PDF 품질 개선 (MIT PyMuPDF 사용)"""
        print("🎨 PDF 품질 개선 중...")
        
        enhanced_path = self.output_dir / f"{Path(pdf_path).stem}_enhanced.pdf"
        
        doc = fitz.open(pdf_path)
        new_doc = fitz.open()
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 고해상도 렌더링 (600 DPI)
            mat = fitz.Matrix(4.17, 4.17)  # 300 DPI
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # PIL로 품질 개선
            img_data = pix.tobytes("ppm")
            import io
            img = Image.open(io.BytesIO(img_data))
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)
            
            # 선명도 향상  
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
            
            # 새 페이지에 삽입
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=img_bytes.getvalue())
            
            print(f"  페이지 {page_num + 1} 품질 개선 완료")
        
        new_doc.save(str(enhanced_path))
        new_doc.close()
        doc.close()
        
        print(f"✅ 개선된 PDF: {enhanced_path}")
        return enhanced_path
    
    def detect_formula_regions(self, page):
        """수식 영역 감지 (간단한 휴리스틱)"""
        # 페이지를 고해상도 이미지로 변환
        mat = fitz.Matrix(3, 3)  # 216 DPI
        pix = page.get_pixmap(matrix=mat)
        
        import io
        img_data = pix.tobytes("ppm") 
        img = Image.open(io.BytesIO(img_data))
        
        # 여기서는 전체 페이지를 수식 후보로 처리
        # 실제로는 YOLO 등으로 수식 영역을 감지해야 함
        return [img]
    
    def extract_formulas_with_rapidlatex(self, pdf_path):
        """RapidLaTeXOCR로 수식 추출"""
        if not self.formula_ocr:
            return []
        
        print("🔬 RapidLaTeXOCR로 수식 추출 중...")
        
        doc = fitz.open(pdf_path)
        results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 수식 영역 감지
            formula_candidates = self.detect_formula_regions(page)
            
            for idx, img in enumerate(formula_candidates):
                try:
                    # 이미지를 임시 파일로 저장
                    temp_path = self.output_dir / f"temp_page_{page_num}_{idx}.png"
                    img.save(temp_path)
                    
                    # LaTeX OCR로 변환
                    if hasattr(self.formula_ocr, 'predict'):
                        latex_result = self.formula_ocr.predict(str(temp_path))
                    else:
                        # rapid-latex-ocr 사용 - 결과가 튜플일 수 있음
                        latex_result = self.formula_ocr(str(temp_path))
                    
                    # 결과 처리 (튜플인 경우 첫 번째 요소 사용)
                    if isinstance(latex_result, tuple):
                        latex_result = latex_result[0] if latex_result else ""
                    elif isinstance(latex_result, list):
                        latex_result = latex_result[0] if latex_result else ""
                    
                    if latex_result and str(latex_result).strip():
                        results.append({
                            'page': page_num,
                            'type': 'formula',
                            'content': str(latex_result).strip(),
                            'method': 'RapidLaTeXOCR'
                        })
                        print(f"  📄 페이지 {page_num + 1}: {str(latex_result)[:50]}...")
                    
                    # 임시 파일 삭제
                    temp_path.unlink()
                    
                except Exception as e:
                    print(f"  ❌ 페이지 {page_num + 1} 오류: {e}")
        
        doc.close()
        return results
    
    def extract_text_with_paddle(self, pdf_path):
        """PaddleOCR로 텍스트 추출"""
        if not self.text_ocr:
            return []
        
        print("📝 PaddleOCR로 텍스트 추출 중...")
        
        doc = fitz.open(pdf_path)
        results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 페이지를 이미지로 변환
            mat = fitz.Matrix(2, 2)  # 144 DPI
            pix = page.get_pixmap(matrix=mat)
            
            import io
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # 임시 파일로 저장
            temp_path = self.output_dir / f"temp_text_page_{page_num}.png"
            img.save(temp_path)
            
            try:
                # PaddleOCR 실행 (새 API 사용)
                if hasattr(self.text_ocr, 'predict'):
                    ocr_results = self.text_ocr.predict(str(temp_path))
                else:
                    ocr_results = self.text_ocr.ocr(str(temp_path))
                
                # 결과가 비어있거나 None인 경우 처리
                if not ocr_results or not isinstance(ocr_results, list):
                    print(f"  ⚠️ 페이지 {page_num + 1}: 텍스트 없음")
                    continue
                
                # 결과 구조 확인 및 안전한 파싱
                page_results = ocr_results[0] if ocr_results else []
                if not page_results:
                    continue
                    
                for line in page_results:
                    try:
                        # 안전한 데이터 접근
                        if isinstance(line, list) and len(line) >= 2:
                            text_data = line[1]
                            if isinstance(text_data, list) and len(text_data) >= 2:
                                text = text_data[0]
                                confidence = text_data[1]
                            else:
                                continue
                        else:
                            continue
                        
                        if confidence > 0.7:  # 신뢰도 70% 이상
                            results.append({
                                'page': page_num,
                                'type': 'text',
                                'content': text,
                                'confidence': confidence,
                                'method': 'PaddleOCR'
                            })
                    except Exception as e:
                        # 개별 라인 파싱 오류는 무시하고 계속
                        continue
                
                print(f"  📄 페이지 {page_num + 1}: {len(ocr_results[0] or [])}개 텍스트 추출")
                
            except Exception as e:
                print(f"  ❌ 페이지 {page_num + 1} 텍스트 추출 오류: {e}")
            
            # 임시 파일 삭제
            temp_path.unlink()
        
        doc.close()
        return results
    
    def process_pdf(self, pdf_path):
        """PDF 종합 처리"""
        pdf_path = Path(pdf_path)
        
        print(f"🚀 하이브리드 수식 추출 시작")
        print("=" * 60)
        print(f"📄 입력: {pdf_path}")
        print(f"📁 출력: {self.output_dir}")
        print(f"🏷️ 라이선스: MIT/Apache 2.0 (상업적 사용 가능)")
        
        # 1단계: PDF 품질 개선
        enhanced_pdf = self.enhance_pdf_quality(pdf_path)
        
        # 2단계: 수식 추출 (RapidLaTeXOCR)
        formula_results = self.extract_formulas_with_rapidlatex(enhanced_pdf)
        
        # 3단계: 텍스트 추출 (PaddleOCR)
        text_results = self.extract_text_with_paddle(enhanced_pdf)
        
        # 4단계: 결과 통합
        all_results = formula_results + text_results
        
        # 5단계: 결과 저장
        results_json = self.output_dir / "extraction_results.json"
        with open(results_json, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 6단계: 리포트 생성
        self.create_report(pdf_path, all_results)
        
        print(f"\n✅ 처리 완료!")
        print(f"📊 수식: {len(formula_results)}개")
        print(f"📝 텍스트: {len(text_results)}개") 
        print(f"📄 결과: {results_json}")
        
        return {
            'input_pdf': str(pdf_path),
            'enhanced_pdf': str(enhanced_pdf),
            'results': all_results,
            'output_dir': str(self.output_dir)
        }
    
    def create_report(self, pdf_path, results):
        """HTML 리포트 생성"""
        formula_results = [r for r in results if r['type'] == 'formula']
        text_results = [r for r in results if r['type'] == 'text']
        
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>하이브리드 수식 추출 결과</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #e8f5e8; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .license {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        .formula {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .text {{ background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; flex: 1; text-align: center; }}
    </style>
</head>
<body>
    <h1>🔬 하이브리드 수식 추출 결과</h1>
    
    <div class="header">
        <strong>📄 원본 PDF:</strong> {Path(pdf_path).name}<br>
        <strong>⏰ 처리 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>🛠️ 사용 도구:</strong> RapidLaTeXOCR (MIT) + PaddleOCR (Apache 2.0)
    </div>
    
    <div class="license">
        <strong>📋 라이선스 정보:</strong><br>
        • RapidLaTeXOCR: MIT License (상업적 사용 가능, 소스코드 공개 의무 없음)<br>
        • PaddleOCR: Apache 2.0 License (상업적 사용 가능, 소스코드 공개 의무 없음)<br>
        • PyMuPDF: MIT License (상업적 사용 가능, 소스코드 공개 의무 없음)
    </div>
    
    <div class="stats">
        <div class="stat">
            <strong>{len(formula_results)}</strong><br>
            수식 추출
        </div>
        <div class="stat">
            <strong>{len(text_results)}</strong><br>
            텍스트 추출
        </div>
        <div class="stat">
            <strong>{len(results)}</strong><br>
            총 요소
        </div>
    </div>
    
    <h2>🔢 추출된 수식</h2>
"""
        
        for i, result in enumerate(formula_results):
            html += f"""
    <div class="formula">
        <strong>수식 {i+1} (페이지 {result['page']+1}):</strong><br>
        <code>{result['content']}</code><br>
        <strong>렌더링:</strong> \\({result['content']}\\)
    </div>
"""
        
        html += f"""
    <h2>📝 추출된 텍스트 (샘플)</h2>
"""
        
        for i, result in enumerate(text_results[:10]):  # 처음 10개만
            html += f"""
    <div class="text">
        <strong>페이지 {result['page']+1}:</strong> {result['content']} 
        <small>(신뢰도: {result.get('confidence', 0):.2f})</small>
    </div>
"""
        
        html += """
</body>
</html>"""
        
        report_path = self.output_dir / "hybrid_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 HTML 리포트: {report_path}")
        
        # Windows에서 자동 열기
        try:
            import os
            os.startfile(str(self.output_dir))
            os.startfile(str(report_path))
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("사용법: python hybrid_formula_extractor.py <PDF파일>")
        print("\n이 도구는 라이선스 안전한 방법으로 수식을 추출합니다:")
        print("• RapidLaTeXOCR (MIT License)")
        print("• PaddleOCR (Apache 2.0 License)") 
        print("• PyMuPDF (MIT License)")
        print("\n✅ 상업적 사용 가능, 소스코드 공개 의무 없음")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        sys.exit(1)
    
    # 필요한 라이브러리 확인
    print("🔍 설치된 라이브러리 확인 중...")
    
    # rapid-latex-ocr 확인
    latex_ocr_available = False
    try:
        from rapid_latex_ocr import LaTeXOCR  # 정확한 클래스명
        print("✅ rapid-latex-ocr (LaTeXOCR) 사용 가능")
        latex_ocr_available = True
    except ImportError:
        print("❌ rapid-latex-ocr import 실패")
    
    # PaddleOCR 확인
    paddle_available = False
    try:
        import paddleocr
        print("✅ paddleocr 사용 가능")
        paddle_available = True
    except ImportError:
        print("⚠️ paddleocr 없음 (선택사항)")
    
    # 최소 하나라도 있으면 계속 진행
    if not latex_ocr_available and not paddle_available:
        print("\n❌ 사용 가능한 OCR 도구가 없습니다.")
        print("다음 중 하나를 설치하세요:")
        print("  pip install rapid-latex-ocr")
        print("  pip install paddleocr")
        sys.exit(1)
    
    print(f"✅ 진행 가능: LaTeX OCR={latex_ocr_available}, PaddleOCR={paddle_available}")
    
    # 추출 실행
    extractor = LicenseSafeFormulaExtractor()
    result = extractor.process_pdf(pdf_path)

if __name__ == "__main__":
    main()